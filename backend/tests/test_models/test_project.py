"""Tests for the Project model."""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project


@pytest.mark.asyncio
async def test_create_project(db_session: AsyncSession) -> None:
    """Test creating a project in the database."""
    project = Project(name="Test Project", description="A test project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    assert project.id is not None
    assert isinstance(project.id, UUID)
    assert project.name == "Test Project"
    assert project.description == "A test project"
    assert project.created_at is not None
    assert project.updated_at is not None


@pytest.mark.asyncio
async def test_project_id_is_uuidv7(db_session: AsyncSession) -> None:
    """Test that project IDs are UUIDv7 (version 7)."""
    project = Project(name="UUID Test", description="Testing UUID version")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    # UUIDv7 has version 7 in the version field
    assert project.id.version == 7


@pytest.mark.asyncio
async def test_project_name_is_unique(db_session: AsyncSession) -> None:
    """Test that project names must be unique."""
    from sqlalchemy.exc import IntegrityError

    project1 = Project(name="Unique Name", description="First project")
    db_session.add(project1)
    await db_session.flush()

    project2 = Project(name="Unique Name", description="Second project")
    db_session.add(project2)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_project_description_is_optional(db_session: AsyncSession) -> None:
    """Test that project description is optional."""
    project = Project(name="No Description")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    assert project.description is None


@pytest.mark.asyncio
async def test_query_project_by_name(db_session: AsyncSession) -> None:
    """Test querying a project by name."""
    project = Project(name="Queryable Project", description="For querying")
    db_session.add(project)
    await db_session.flush()

    result = await db_session.execute(select(Project).where(Project.name == "Queryable Project"))
    found_project = result.scalar_one()

    assert found_project.id == project.id
    assert found_project.name == "Queryable Project"


@pytest.mark.asyncio
async def test_update_project(db_session: AsyncSession) -> None:
    """Test updating a project."""
    project = Project(name="Original Name", description="Original description")
    db_session.add(project)
    await db_session.flush()
    original_updated_at = project.updated_at

    project.name = "Updated Name"
    project.description = "Updated description"
    await db_session.flush()
    await db_session.refresh(project)

    assert project.name == "Updated Name"
    assert project.description == "Updated description"
    # Note: updated_at auto-update depends on implementation


@pytest.mark.asyncio
async def test_delete_project(db_session: AsyncSession) -> None:
    """Test deleting a project."""
    project = Project(name="To Delete", description="Will be deleted")
    db_session.add(project)
    await db_session.flush()
    project_id = project.id

    await db_session.delete(project)
    await db_session.flush()

    result = await db_session.execute(select(Project).where(Project.id == project_id))
    assert result.scalar_one_or_none() is None
