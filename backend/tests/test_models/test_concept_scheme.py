"""Tests for the ConceptScheme model."""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project", description="For testing schemes")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_create_concept_scheme(db_session: AsyncSession, project: Project) -> None:
    """Test creating a concept scheme."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        description="A test scheme",
        uri="http://example.org/schemes/test",
        publisher="Test Publisher",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    assert scheme.id is not None
    assert isinstance(scheme.id, UUID)
    assert scheme.project_id == project.id
    assert scheme.title == "Test Scheme"
    assert scheme.description == "A test scheme"
    assert scheme.uri == "http://example.org/schemes/test"
    assert scheme.publisher == "Test Publisher"
    assert scheme.created_at is not None
    assert scheme.updated_at is not None


@pytest.mark.asyncio
async def test_concept_scheme_id_is_uuidv7(db_session: AsyncSession, project: Project) -> None:
    """Test that concept scheme IDs are UUIDv7."""
    scheme = ConceptScheme(project_id=project.id, title="UUID Test")
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    assert scheme.id.version == 7


@pytest.mark.asyncio
async def test_concept_scheme_title_required(db_session: AsyncSession, project: Project) -> None:
    """Test that scheme title is required."""
    from sqlalchemy.exc import IntegrityError

    scheme = ConceptScheme(project_id=project.id, title=None)  # type: ignore[arg-type]
    db_session.add(scheme)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_concept_scheme_optional_fields(db_session: AsyncSession, project: Project) -> None:
    """Test that description, uri, publisher are optional."""
    scheme = ConceptScheme(project_id=project.id, title="Minimal Scheme")
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    assert scheme.description is None
    assert scheme.uri is None
    assert scheme.publisher is None


@pytest.mark.asyncio
async def test_concept_scheme_belongs_to_project(
    db_session: AsyncSession, project: Project
) -> None:
    """Test that scheme has a relationship to project."""
    scheme = ConceptScheme(project_id=project.id, title="Related Scheme")
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)

    # Access the project relationship
    assert scheme.project.id == project.id
    assert scheme.project.name == "Test Project"


@pytest.mark.asyncio
async def test_project_has_many_schemes(db_session: AsyncSession, project: Project) -> None:
    """Test that a project can have multiple schemes."""
    scheme1 = ConceptScheme(project_id=project.id, title="Scheme 1")
    scheme2 = ConceptScheme(project_id=project.id, title="Scheme 2")
    db_session.add_all([scheme1, scheme2])
    await db_session.flush()

    # Refresh project to get schemes
    await db_session.refresh(project)
    assert len(project.schemes) == 2


@pytest.mark.asyncio
async def test_unique_title_per_project(db_session: AsyncSession, project: Project) -> None:
    """Test that scheme titles must be unique within a project."""
    from sqlalchemy.exc import IntegrityError

    scheme1 = ConceptScheme(project_id=project.id, title="Duplicate Title")
    db_session.add(scheme1)
    await db_session.flush()

    scheme2 = ConceptScheme(project_id=project.id, title="Duplicate Title")
    db_session.add(scheme2)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_same_title_different_projects(db_session: AsyncSession) -> None:
    """Test that same title can exist in different projects."""
    project1 = Project(name="Project 1")
    project2 = Project(name="Project 2")
    db_session.add_all([project1, project2])
    await db_session.flush()

    scheme1 = ConceptScheme(project_id=project1.id, title="Same Title")
    scheme2 = ConceptScheme(project_id=project2.id, title="Same Title")
    db_session.add_all([scheme1, scheme2])
    await db_session.flush()

    # Should not raise
    assert scheme1.title == scheme2.title
    assert scheme1.project_id != scheme2.project_id


@pytest.mark.asyncio
async def test_cascade_delete_with_project(db_session: AsyncSession, project: Project) -> None:
    """Test that schemes are deleted when project is deleted."""
    scheme = ConceptScheme(project_id=project.id, title="To Delete")
    db_session.add(scheme)
    await db_session.flush()
    scheme_id = scheme.id

    await db_session.delete(project)
    await db_session.flush()

    result = await db_session.execute(
        select(ConceptScheme).where(ConceptScheme.id == scheme_id)
    )
    assert result.scalar_one_or_none() is None
