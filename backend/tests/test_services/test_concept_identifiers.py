"""Tests for concept identifier auto-allocation and rejection."""

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.concept import ConceptCreate, ConceptUpdate
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.identifier_service import PrefixRequiredError


@pytest.fixture
async def project_with_prefix(db_session: AsyncSession) -> Project:
    project = Project(name="Concept ID Project", identifier_prefix="TST")
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
        title="Concept ID Scheme",
        uri="http://example.org/s",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


async def test_create_concept_auto_assigns_identifier(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    service = ConceptService(db_session)
    concept = await service.create_concept(
        scheme.id, ConceptCreate(pref_label="Auto ID")
    )
    assert concept.identifier == "TST000001"


async def test_create_concept_increments_across_calls(
    db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    service = ConceptService(db_session)
    c1 = await service.create_concept(
        scheme.id, ConceptCreate(pref_label="First")
    )
    c2 = await service.create_concept(
        scheme.id, ConceptCreate(pref_label="Second")
    )
    assert c1.identifier == "TST000001"
    assert c2.identifier == "TST000002"


async def test_create_concept_without_prefix_raises(
    db_session: AsyncSession,
) -> None:
    project = Project(name="No Prefix Concept")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    scheme = ConceptScheme(
        project_id=project.id, title="S", uri="http://example.org/s"
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    service = ConceptService(db_session)
    with pytest.raises(PrefixRequiredError):
        await service.create_concept(
            scheme.id, ConceptCreate(pref_label="No Prefix")
        )


def test_update_concept_has_no_identifier_field() -> None:
    """ConceptUpdate should not have an identifier field."""
    assert "identifier" not in ConceptUpdate.model_fields


def test_create_rejects_identifier_field() -> None:
    """Stale clients sending identifier on create should be rejected."""
    with pytest.raises(ValidationError, match="identifier"):
        ConceptCreate(pref_label="Test", identifier="legacy-id")


def test_update_rejects_identifier_field() -> None:
    """Stale clients sending identifier on update should be rejected."""
    with pytest.raises(ValidationError, match="identifier"):
        ConceptUpdate(pref_label="Test", identifier="legacy-id")
