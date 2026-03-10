"""Tests for IdentifierService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.services.identifier_service import (
    CounterOverflowError,
    IdentifierService,
    PrefixRequiredError,
)


@pytest.fixture
async def project_with_prefix(db_session: AsyncSession) -> Project:
    project = Project(name="ID Service Project", identifier_prefix="EVD")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def scheme(
    db_session: AsyncSession, project_with_prefix: Project
) -> ConceptScheme:
    scheme = ConceptScheme(
        project_id=project_with_prefix.id,
        title="ID Scheme",
        uri="http://example.org/s",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


async def test_allocate_returns_prefixed_identifier(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    service = IdentifierService(db_session)
    identifier = await service.allocate(project_with_prefix.id)
    assert identifier == "EVD000001"


async def test_allocate_increments_counter(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    service = IdentifierService(db_session)
    id1 = await service.allocate(project_with_prefix.id)
    id2 = await service.allocate(project_with_prefix.id)
    assert id1 == "EVD000001"
    assert id2 == "EVD000002"


async def test_allocate_without_prefix_raises(
    db_session: AsyncSession,
) -> None:
    project = Project(name="No Prefix Alloc")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    service = IdentifierService(db_session)
    with pytest.raises(PrefixRequiredError):
        await service.allocate(project.id)

    await db_session.refresh(project)
    assert project.identifier_counter == 0


async def test_allocate_overflow_raises(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Counter at 999999 -> next allocation should raise."""
    project_with_prefix.identifier_counter = 999999
    await db_session.flush()

    service = IdentifierService(db_session)
    with pytest.raises(CounterOverflowError):
        await service.allocate(project_with_prefix.id)

    await db_session.refresh(project_with_prefix)
    assert project_with_prefix.identifier_counter == 999999


class TestValidateImported:
    async def test_detects_duplicates_within_list(
        self, db_session: AsyncSession, project_with_prefix: Project
    ) -> None:
        service = IdentifierService(db_session)
        conflicts = await service.validate_imported(
            project_with_prefix.id, ["EVD000001", "EVD000001", "EVD000001"]
        )
        dupes = [c for c in conflicts if c["type"] == "duplicate_in_file"]
        assert len(dupes) == 1
        assert dupes[0]["identifier"] == "EVD000001"

    async def test_detects_collision_with_existing(
        self,
        db_session: AsyncSession,
        project_with_prefix: Project,
        scheme: ConceptScheme,
    ) -> None:
        concept = Concept(
            scheme_id=scheme.id,
            pref_label="Existing",
            identifier="EVD000001",
        )
        db_session.add(concept)
        await db_session.flush()

        service = IdentifierService(db_session)
        conflicts = await service.validate_imported(
            project_with_prefix.id, ["EVD000001", "EVD000002"]
        )
        assert len(conflicts) == 1
        assert conflicts[0]["identifier"] == "EVD000001"
        assert conflicts[0]["type"] == "collision"

    async def test_no_conflicts_for_unique_identifiers(
        self, db_session: AsyncSession, project_with_prefix: Project
    ) -> None:
        service = IdentifierService(db_session)
        conflicts = await service.validate_imported(
            project_with_prefix.id, ["NEW001", "NEW002"]
        )
        assert conflicts == []


class TestReconcileCounter:
    async def test_advances_counter_to_max_matching_identifier(
        self, db_session: AsyncSession, project_with_prefix: Project
    ) -> None:
        service = IdentifierService(db_session)
        await service.reconcile_counter(
            project_with_prefix.id, ["EVD000042", "EVD000010"]
        )
        await db_session.refresh(project_with_prefix)
        assert project_with_prefix.identifier_counter == 42

    async def test_does_not_move_counter_backward(
        self, db_session: AsyncSession, project_with_prefix: Project
    ) -> None:
        project_with_prefix.identifier_counter = 100
        await db_session.flush()

        service = IdentifierService(db_session)
        await service.reconcile_counter(
            project_with_prefix.id, ["EVD000042"]
        )
        await db_session.refresh(project_with_prefix)
        assert project_with_prefix.identifier_counter == 100

    async def test_ignores_non_matching_prefixes(
        self, db_session: AsyncSession, project_with_prefix: Project
    ) -> None:
        service = IdentifierService(db_session)
        await service.reconcile_counter(
            project_with_prefix.id, ["OTHER001", "CAT000050"]
        )
        await db_session.refresh(project_with_prefix)
        assert project_with_prefix.identifier_counter == 0

    async def test_skips_when_no_prefix_set(
        self, db_session: AsyncSession
    ) -> None:
        project = Project(name="No Prefix Reconcile")
        db_session.add(project)
        await db_session.flush()
        await db_session.refresh(project)

        service = IdentifierService(db_session)
        await service.reconcile_counter(project.id, ["EVD000042"])
        await db_session.refresh(project)
        assert project.identifier_counter == 0

    async def test_case_sensitive_prefix_match(
        self, db_session: AsyncSession, project_with_prefix: Project
    ) -> None:
        """evd000042 should NOT match prefix EVD."""
        service = IdentifierService(db_session)
        await service.reconcile_counter(
            project_with_prefix.id, ["evd000042"]
        )
        await db_session.refresh(project_with_prefix)
        assert project_with_prefix.identifier_counter == 0
