"""Tests for the ProjectService."""

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.project import ProjectCreate, ProjectUpdate
from taxonomy_builder.services.project_service import (
    ProjectNotFoundError,
    ProjectNameExistsError,
    ProjectService,
)


@pytest.mark.asyncio
async def test_list_projects_empty(db_session: AsyncSession) -> None:
    """Test listing projects when none exist."""
    service = ProjectService(db_session)
    projects = await service.list_projects()
    assert projects == []


@pytest.mark.asyncio
async def test_list_projects(db_session: AsyncSession) -> None:
    """Test listing projects."""
    service = ProjectService(db_session)

    # Create some projects
    await service.create_project(ProjectCreate(name="Project A"))
    await service.create_project(ProjectCreate(name="Project B"))

    projects = await service.list_projects()
    assert len(projects) == 2
    # Should be ordered by name
    assert projects[0].name == "Project A"
    assert projects[1].name == "Project B"


@pytest.mark.asyncio
async def test_create_project(db_session: AsyncSession) -> None:
    """Test creating a project."""
    service = ProjectService(db_session)
    project_in = ProjectCreate(name="New Project", description="A new project")

    project = await service.create_project(project_in)

    assert project.id is not None
    assert isinstance(project.id, UUID)
    assert project.name == "New Project"
    assert project.description == "A new project"
    assert project.created_at is not None
    assert project.updated_at is not None


@pytest.mark.asyncio
async def test_create_project_without_description(db_session: AsyncSession) -> None:
    """Test creating a project without description."""
    service = ProjectService(db_session)
    project_in = ProjectCreate(name="No Description")

    project = await service.create_project(project_in)

    assert project.name == "No Description"
    assert project.description is None


@pytest.mark.asyncio
async def test_create_project_duplicate_name_raises(db_session: AsyncSession) -> None:
    """Test that creating a project with duplicate name raises error."""
    service = ProjectService(db_session)
    await service.create_project(ProjectCreate(name="Duplicate"))

    with pytest.raises(ProjectNameExistsError) as exc_info:
        await service.create_project(ProjectCreate(name="Duplicate"))

    assert "Duplicate" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_project(db_session: AsyncSession) -> None:
    """Test getting a project by ID."""
    service = ProjectService(db_session)
    created = await service.create_project(
        ProjectCreate(name="Get Test", description="For getting")
    )

    project = await service.get_project(created.id)

    assert project.id == created.id
    assert project.name == "Get Test"
    assert project.description == "For getting"


@pytest.mark.asyncio
async def test_get_project_not_found_raises(db_session: AsyncSession) -> None:
    """Test that getting a non-existent project raises error."""
    service = ProjectService(db_session)
    fake_id = UUID("01234567-89ab-7def-8123-456789abcdef")

    with pytest.raises(ProjectNotFoundError) as exc_info:
        await service.get_project(fake_id)

    assert str(fake_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_project(db_session: AsyncSession) -> None:
    """Test updating a project."""
    service = ProjectService(db_session)
    created = await service.create_project(
        ProjectCreate(name="Original", description="Original description")
    )

    project = await service.update_project(
        created.id,
        ProjectUpdate(name="Updated", description="Updated description"),
    )

    assert project.id == created.id
    assert project.name == "Updated"
    assert project.description == "Updated description"


@pytest.mark.asyncio
async def test_update_project_partial(db_session: AsyncSession) -> None:
    """Test partially updating a project (only name)."""
    service = ProjectService(db_session)
    created = await service.create_project(
        ProjectCreate(name="Original", description="Keep this")
    )

    project = await service.update_project(created.id, ProjectUpdate(name="New Name"))

    assert project.name == "New Name"
    assert project.description == "Keep this"


@pytest.mark.asyncio
async def test_update_project_not_found_raises(db_session: AsyncSession) -> None:
    """Test that updating a non-existent project raises error."""
    service = ProjectService(db_session)
    fake_id = UUID("01234567-89ab-7def-8123-456789abcdef")

    with pytest.raises(ProjectNotFoundError):
        await service.update_project(fake_id, ProjectUpdate(name="New Name"))


@pytest.mark.asyncio
async def test_update_project_duplicate_name_raises(db_session: AsyncSession) -> None:
    """Test that updating to a duplicate name raises error."""
    service = ProjectService(db_session)
    await service.create_project(ProjectCreate(name="Existing"))
    created = await service.create_project(ProjectCreate(name="To Update"))

    with pytest.raises(ProjectNameExistsError):
        await service.update_project(created.id, ProjectUpdate(name="Existing"))


@pytest.mark.asyncio
async def test_delete_project(db_session: AsyncSession) -> None:
    """Test deleting a project."""
    service = ProjectService(db_session)
    created = await service.create_project(ProjectCreate(name="To Delete"))

    await service.delete_project(created.id)

    with pytest.raises(ProjectNotFoundError):
        await service.get_project(created.id)


@pytest.mark.asyncio
async def test_delete_project_not_found_raises(db_session: AsyncSession) -> None:
    """Test that deleting a non-existent project raises error."""
    service = ProjectService(db_session)
    fake_id = UUID("01234567-89ab-7def-8123-456789abcdef")

    with pytest.raises(ProjectNotFoundError):
        await service.delete_project(fake_id)
