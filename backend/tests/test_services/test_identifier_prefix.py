"""Tests for identifier prefix mutability policy on Project."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.project import ProjectCreate, ProjectUpdate
from taxonomy_builder.services.project_service import (
    PrefixLockedError,
    ProjectService,
)


async def test_project_prefix_nullable(db_session: AsyncSession) -> None:
    project = Project(name="No Prefix Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    assert project.identifier_prefix is None
    assert project.identifier_counter == 0


# --- Service: prefix mutability policy ---


async def test_prefix_change_allowed_when_no_identifiers(
    db_session: AsyncSession,
) -> None:
    project = Project(name="Mutable Prefix Project", identifier_prefix="OLD")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    service = ProjectService(db_session)
    updated = await service.update_project(
        project.id, ProjectUpdate(identifier_prefix="NEW")
    )
    assert updated.identifier_prefix == "NEW"


async def test_prefix_change_blocked_when_identifiers_exist(
    db_session: AsyncSession,
    locked_prefix_project: Project,
) -> None:
    service = ProjectService(db_session)
    with pytest.raises(PrefixLockedError):
        await service.update_project(
            locked_prefix_project.id, ProjectUpdate(identifier_prefix="NEW")
        )


async def test_prefix_set_blocked_after_import_without_prefix(
    db_session: AsyncSession,
) -> None:
    """Setting prefix is blocked when imported concepts already have identifiers."""
    project = Project(name="No Prefix Import Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    scheme = ConceptScheme(
        project_id=project.id, title="Imported Scheme", uri="http://example.org/s"
    )
    db_session.add(scheme)
    await db_session.flush()

    # Simulate imported concept with preserved identifier (no prefix on project)
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Imported Concept",
        identifier="C00170",
    )
    db_session.add(concept)
    await db_session.flush()

    service = ProjectService(db_session)
    with pytest.raises(PrefixLockedError):
        await service.update_project(
            project.id, ProjectUpdate(identifier_prefix="C")
        )


async def test_create_project_with_prefix(db_session: AsyncSession) -> None:
    service = ProjectService(db_session)
    project = await service.create_project(
        ProjectCreate(name="Created With Prefix", identifier_prefix="TST")
    )
    assert project.identifier_prefix == "TST"
    assert project.identifier_counter == 0
