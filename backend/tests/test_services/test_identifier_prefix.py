"""Tests for identifier prefix and counter on Project."""

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from taxonomy_builder.services.project_service import (
    PrefixLockedError,
    ProjectService,
)


@pytest.fixture
async def project_with_prefix(db_session: AsyncSession) -> Project:
    """Create a project with identifier prefix configured."""
    project = Project(name="Prefixed Project", identifier_prefix="EVD")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


async def test_project_prefix_and_counter_persisted(
    project_with_prefix: Project,
) -> None:
    assert project_with_prefix.identifier_prefix == "EVD"
    assert project_with_prefix.identifier_counter == 0


async def test_project_prefix_nullable(db_session: AsyncSession) -> None:
    project = Project(name="No Prefix Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    assert project.identifier_prefix is None
    assert project.identifier_counter == 0


# --- Schema validation ---


@pytest.mark.parametrize("prefix", ["C", "EVD", "ABCD"])
def test_create_accepts_valid_prefix(prefix: str) -> None:
    p = ProjectCreate(name="Test", identifier_prefix=prefix)
    assert p.identifier_prefix == prefix


@pytest.mark.parametrize("prefix", ["evd", "ABCDE", "", "AB1"])
def test_create_rejects_invalid_prefix(prefix: str) -> None:
    with pytest.raises(ValidationError, match="identifier_prefix"):
        ProjectCreate(name="Test", identifier_prefix=prefix)


def test_create_prefix_defaults_to_none() -> None:
    assert ProjectCreate(name="Test").identifier_prefix is None


def test_update_accepts_valid_prefix() -> None:
    assert ProjectUpdate(identifier_prefix="ABC").identifier_prefix == "ABC"


def test_read_includes_prefix_and_counter() -> None:
    p = ProjectRead(
        id="01234567-0123-0123-0123-012345678901",
        name="Test",
        description=None,
        namespace=None,
        identifier_prefix="EVD",
        identifier_counter=42,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )
    assert p.identifier_prefix == "EVD"
    assert p.identifier_counter == 42


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
) -> None:
    project = Project(name="Locked Prefix Project", identifier_prefix="EVD")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    scheme = ConceptScheme(
        project_id=project.id, title="Scheme", uri="http://example.org/s"
    )
    db_session.add(scheme)
    await db_session.flush()

    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Has Identifier",
        identifier="EVD000001",
    )
    db_session.add(concept)
    await db_session.flush()

    service = ProjectService(db_session)
    with pytest.raises(PrefixLockedError):
        await service.update_project(
            project.id, ProjectUpdate(identifier_prefix="NEW")
        )


async def test_prefix_set_blocked_after_import_without_prefix(
    db_session: AsyncSession,
) -> None:
    """Project started with no prefix, imported concepts have identifiers, then user tries to set prefix."""
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
