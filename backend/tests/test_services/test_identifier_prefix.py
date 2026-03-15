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


async def test_project_prefix_and_counter_persisted(
    project_with_prefix: Project,
) -> None:
    assert project_with_prefix.identifier_prefix == "EVD"
    assert project_with_prefix.identifier_counter == 0


async def test_project_prefix_nullable(db_session: AsyncSession) -> None:
    project = Project(
        name="No Prefix Project",
        namespace="https://example.org/vocab",
        identifier_prefix="TST",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    assert project.identifier_prefix == "TST"
    assert project.identifier_counter == 0


# --- Schema validation ---


@pytest.mark.parametrize("prefix", ["C", "EVD", "ABCD"])
def test_create_accepts_valid_prefix(prefix: str) -> None:
    p = ProjectCreate(name="Test", namespace="https://example.org/vocab", identifier_prefix=prefix)
    assert p.identifier_prefix == prefix


@pytest.mark.parametrize("prefix", ["evd", "ABCDE", "", "AB1"])
def test_create_rejects_invalid_prefix(prefix: str) -> None:
    with pytest.raises(ValidationError, match="identifier_prefix"):
        ProjectCreate(name="Test", namespace="https://example.org/vocab", identifier_prefix=prefix)



def test_update_accepts_valid_prefix() -> None:
    assert ProjectUpdate(identifier_prefix="ABC").identifier_prefix == "ABC"


def test_read_includes_prefix_counter_and_locked() -> None:
    p = ProjectRead(
        id="01234567-0123-0123-0123-012345678901",
        name="Test",
        description=None,
        namespace="https://example.org/vocab",
        identifier_prefix="EVD",
        identifier_counter=42,
        prefix_locked=True,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )
    assert p.identifier_prefix == "EVD"
    assert p.identifier_counter == 42
    assert p.prefix_locked is True


# --- Service: prefix mutability policy ---


async def test_prefix_change_allowed_when_no_identifiers(
    db_session: AsyncSession,
) -> None:
    project = Project(
        name="Mutable Prefix Project",
        namespace="https://example.org/vocab",
        identifier_prefix="OLD",
    )
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
    project = Project(
        name="Locked Prefix Project",
        namespace="https://example.org/vocab",
        identifier_prefix="EVD",
    )
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


async def test_prefix_change_allowed_when_concepts_dont_match_prefix(
    db_session: AsyncSession,
) -> None:
    """Changing prefix is allowed when existing concepts don't match the current prefix."""
    project = Project(
        name="Non-Matching Import Project",
        namespace="https://example.org/vocab",
        identifier_prefix="TST",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    scheme = ConceptScheme(
        project_id=project.id, title="Imported Scheme", uri="http://example.org/s"
    )
    db_session.add(scheme)
    await db_session.flush()

    # Imported concept with identifier that doesn't match project prefix "TST"
    concept = Concept(
        scheme_id=scheme.id,
        pref_label="Imported Concept",
        identifier="C00170",
    )
    db_session.add(concept)
    await db_session.flush()

    service = ProjectService(db_session)
    updated = await service.update_project(
        project.id, ProjectUpdate(identifier_prefix="NEW")
    )
    assert updated.identifier_prefix == "NEW"


async def test_create_project_with_prefix(db_session: AsyncSession) -> None:
    service = ProjectService(db_session)
    project = await service.create_project(
        ProjectCreate(
            name="Created With Prefix",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
    )
    assert project.identifier_prefix == "TST"
    assert project.identifier_counter == 0


# --- prefix_locked ---


async def test_prefix_locked_false_for_new_project(
    db_session: AsyncSession, project_with_prefix: Project,
) -> None:
    """New project with no concepts has prefix_locked=False."""
    service = ProjectService(db_session)
    project = await service.get_project(project_with_prefix.id)
    assert project.prefix_locked is False


async def test_prefix_locked_true_when_matching_concepts_exist(
    db_session: AsyncSession,
) -> None:
    """Project with concepts matching prefix has prefix_locked=True."""
    project = Project(
        name="Locked Project",
        namespace="https://example.org/locked/",
        identifier_prefix="EVD",
    )
    db_session.add(project)
    await db_session.flush()

    scheme = ConceptScheme(
        project_id=project.id, title="Scheme", uri="http://example.org/s"
    )
    db_session.add(scheme)
    await db_session.flush()

    concept = Concept(
        scheme_id=scheme.id, pref_label="Test", identifier="EVD000001"
    )
    db_session.add(concept)
    await db_session.flush()

    service = ProjectService(db_session)
    result = await service.get_project(project.id)
    assert result.prefix_locked is True


async def test_prefix_locked_false_when_non_matching_concepts_exist(
    db_session: AsyncSession,
) -> None:
    """Project with concepts NOT matching prefix has prefix_locked=False."""
    project = Project(
        name="Unlocked Project",
        namespace="https://example.org/unlocked/",
        identifier_prefix="EVD",
    )
    db_session.add(project)
    await db_session.flush()

    scheme = ConceptScheme(
        project_id=project.id, title="Scheme", uri="http://example.org/s"
    )
    db_session.add(scheme)
    await db_session.flush()

    # Concept identifier doesn't match prefix "EVD"
    concept = Concept(
        scheme_id=scheme.id, pref_label="Imported", identifier="C00170"
    )
    db_session.add(concept)
    await db_session.flush()

    service = ProjectService(db_session)
    result = await service.get_project(project.id)
    assert result.prefix_locked is False
