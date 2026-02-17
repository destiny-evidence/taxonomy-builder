"""Tests for the ConceptScheme model."""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from tests.factories import ConceptSchemeFactory, ProjectFactory, flush


@pytest.mark.asyncio
async def test_create_concept_scheme(db_session: AsyncSession) -> None:
    """Test creating a concept scheme."""
    scheme = await flush(
        db_session,
        ConceptSchemeFactory.create(
            title="Test Scheme",
            description="A test scheme",
            uri="http://example.org/schemes/test",
        ),
    )

    assert scheme.id is not None
    assert isinstance(scheme.id, UUID)
    assert scheme.project_id is not None
    assert scheme.title == "Test Scheme"
    assert scheme.description == "A test scheme"
    assert scheme.uri == "http://example.org/schemes/test"
    assert scheme.created_at is not None
    assert scheme.updated_at is not None


@pytest.mark.asyncio
async def test_concept_scheme_id_is_uuidv7(db_session: AsyncSession) -> None:
    """Test that concept scheme IDs are UUIDv7."""
    scheme = await flush(db_session, ConceptSchemeFactory.create())

    assert scheme.id.version == 7


@pytest.mark.asyncio
async def test_concept_scheme_title_required(db_session: AsyncSession) -> None:
    """Test that scheme title is required."""
    from sqlalchemy.exc import IntegrityError

    project = await flush(db_session, ProjectFactory.create())
    scheme = ConceptScheme(project_id=project.id, title=None)  # type: ignore[arg-type]
    db_session.add(scheme)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_concept_scheme_optional_fields(db_session: AsyncSession) -> None:
    """Test that description and uri are optional."""
    scheme = await flush(
        db_session, ConceptSchemeFactory.create(description=None, uri=None)
    )

    assert scheme.description is None
    assert scheme.uri is None


@pytest.mark.asyncio
async def test_concept_scheme_belongs_to_project(db_session: AsyncSession) -> None:
    """Test that scheme has a relationship to project."""
    project = ProjectFactory.create(name="Test Project")
    scheme = await flush(db_session, ConceptSchemeFactory.create(project=project))

    assert scheme.project.id == project.id
    assert scheme.project.name == "Test Project"


@pytest.mark.asyncio
async def test_project_has_many_schemes(db_session: AsyncSession) -> None:
    """Test that a project can have multiple schemes."""
    project = ProjectFactory.create()
    ConceptSchemeFactory.create(project=project, title="Scheme 1")
    ConceptSchemeFactory.create(project=project, title="Scheme 2")
    await db_session.flush()

    await db_session.refresh(project)
    assert len(project.schemes) == 2


@pytest.mark.asyncio
async def test_unique_title_per_project(db_session: AsyncSession) -> None:
    """Test that scheme titles must be unique within a project."""
    from sqlalchemy.exc import IntegrityError

    project = ProjectFactory.create()
    await flush(
        db_session, ConceptSchemeFactory.create(project=project, title="Duplicate Title")
    )

    ConceptSchemeFactory.create(project=project, title="Duplicate Title")

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_same_title_different_projects(db_session: AsyncSession) -> None:
    """Test that same title can exist in different projects."""
    scheme1 = ConceptSchemeFactory.create(title="Same Title")
    scheme2 = ConceptSchemeFactory.create(title="Same Title")
    await db_session.flush()

    # Should not raise
    assert scheme1.title == scheme2.title
    assert scheme1.project_id != scheme2.project_id


@pytest.mark.asyncio
async def test_cascade_delete_with_project(db_session: AsyncSession) -> None:
    """Test that schemes are deleted when project is deleted."""
    scheme = await flush(db_session, ConceptSchemeFactory.create())
    scheme_id = scheme.id
    project = scheme.project

    await db_session.delete(project)
    await db_session.flush()

    result = await db_session.execute(
        select(ConceptScheme).where(ConceptScheme.id == scheme_id)
    )
    assert result.scalar_one_or_none() is None
