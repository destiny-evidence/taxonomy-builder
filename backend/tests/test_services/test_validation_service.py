"""Tests for the ValidationService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.project_service import ProjectNotFoundError, ProjectService
from taxonomy_builder.services.publishing_service import PublishingService
from taxonomy_builder.services.snapshot_service import SnapshotService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Validation Test Project", namespace="http://example.org/vocab")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a scheme with a URI."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        uri="http://example.org/scheme",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


def service(db_session: AsyncSession) -> PublishingService:
    db_session.expunge_all()
    project_service = ProjectService(db_session)
    concept_service = ConceptService(db_session)
    snapshot_service = SnapshotService(db_session, project_service, concept_service)
    return PublishingService(db_session, project_service, snapshot_service)


@pytest.mark.asyncio
async def test_valid_project(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """A project with a scheme that has a URI and a concept with pref_label is valid."""
    db_session.add(Concept(scheme_id=scheme.id, pref_label="Term A"))
    await db_session.flush()

    result = await service(db_session).validate(project.id)

    assert result.valid is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_project_not_found(db_session: AsyncSession) -> None:
    """Validation raises ProjectNotFoundError for nonexistent project."""
    from uuid import uuid4

    with pytest.raises(ProjectNotFoundError):
        await service(db_session).validate(uuid4())


@pytest.mark.asyncio
async def test_no_schemes(db_session: AsyncSession, project: Project) -> None:
    """A project with no schemes fails validation."""
    result = await service(db_session).validate(project.id)

    assert result.valid is False
    assert any(e.code == "no_schemes" for e in result.errors)


@pytest.mark.asyncio
async def test_no_concepts(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """A project with schemes but no concepts fails validation."""
    result = await service(db_session).validate(project.id)

    assert result.valid is False
    assert any(e.code == "no_concepts" for e in result.errors)


@pytest.mark.asyncio
async def test_scheme_missing_uri(db_session: AsyncSession, project: Project) -> None:
    """A scheme without a URI produces an error."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="No URI Scheme",
        uri=None,
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    db_session.add(Concept(scheme_id=scheme.id, pref_label="Term"))
    await db_session.flush()

    result = await service(db_session).validate(project.id)

    assert result.valid is False
    uri_errors = [e for e in result.errors if e.code == "scheme_missing_uri"]
    assert len(uri_errors) == 1
    assert uri_errors[0].entity_id == scheme.id
    assert uri_errors[0].entity_label == "No URI Scheme"


@pytest.mark.asyncio
async def test_concept_missing_pref_label(
    db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """A concept with an empty pref_label produces an error.

    The DB column is NOT NULL, but a whitespace-only label should be caught.
    """
    db_session.add(Concept(scheme_id=scheme.id, pref_label="   "))
    await db_session.flush()

    result = await service(db_session).validate(project.id)

    assert result.valid is False
    assert any(e.code == "concept_missing_pref_label" for e in result.errors)


@pytest.mark.asyncio
async def test_collects_all_errors(db_session: AsyncSession, project: Project) -> None:
    """Validation returns all errors, not just the first one."""
    # Scheme with no URI
    scheme = ConceptScheme(project_id=project.id, title="No URI", uri=None)
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    # Concept with blank label
    db_session.add(Concept(scheme_id=scheme.id, pref_label="  "))
    await db_session.flush()

    result = await service(db_session).validate(project.id)

    assert result.valid is False
    codes = {e.code for e in result.errors}
    assert "scheme_missing_uri" in codes
    assert "concept_missing_pref_label" in codes


@pytest.mark.asyncio
async def test_multiple_schemes_mixed_validity(
    db_session: AsyncSession, project: Project
) -> None:
    """One valid scheme and one invalid scheme produces errors only for the invalid one."""
    good = ConceptScheme(
        project_id=project.id, title="Good", uri="http://example.org/good"
    )
    bad = ConceptScheme(project_id=project.id, title="Bad", uri=None)
    db_session.add_all([good, bad])
    await db_session.flush()
    await db_session.refresh(good)
    await db_session.refresh(bad)

    db_session.add(Concept(scheme_id=good.id, pref_label="Valid Term"))
    db_session.add(Concept(scheme_id=bad.id, pref_label="Also Valid Term"))
    await db_session.flush()

    result = await service(db_session).validate(project.id)

    assert result.valid is False
    uri_errors = [e for e in result.errors if e.code == "scheme_missing_uri"]
    assert len(uri_errors) == 1
    assert uri_errors[0].entity_id == bad.id
