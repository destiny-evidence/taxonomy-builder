"""Tests for the ProjectService."""

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.project import ProjectCreate, ProjectUpdate
from taxonomy_builder.services.project_service import (
    MAX_COUNTER,
    IdentifierAllocationError,
    ProjectNameExistsError,
    ProjectNotFoundError,
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
    await service.create_project(
        ProjectCreate(
            name="Project A",
            namespace="https://example.org/a/",
            identifier_prefix="TST",
        )
    )
    await service.create_project(
        ProjectCreate(
            name="Project B",
            namespace="https://example.org/b/",
            identifier_prefix="TST",
        )
    )

    projects = await service.list_projects()
    assert len(projects) == 2
    # Should be ordered by name
    assert projects[0].name == "Project A"
    assert projects[1].name == "Project B"


@pytest.mark.asyncio
async def test_create_project(db_session: AsyncSession) -> None:
    """Test creating a project."""
    service = ProjectService(db_session)
    project_in = ProjectCreate(
        name="New Project",
        description="A new project",
        namespace="https://example.org/vocab",
        identifier_prefix="TST",
    )

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
    project_in = ProjectCreate(
        name="No Description",
        namespace="https://example.org/vocab",
        identifier_prefix="TST",
    )

    project = await service.create_project(project_in)

    assert project.name == "No Description"
    assert project.description is None


@pytest.mark.asyncio
async def test_create_project_duplicate_name_raises(db_session: AsyncSession) -> None:
    """Test that creating a project with duplicate name raises error."""
    service = ProjectService(db_session)
    await service.create_project(
        ProjectCreate(
            name="Duplicate",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
    )

    with pytest.raises(ProjectNameExistsError) as exc_info:
        await service.create_project(
            ProjectCreate(
                name="Duplicate",
                namespace="https://example.org/vocab",
                identifier_prefix="TST",
            )
        )

    assert "Duplicate" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_project(db_session: AsyncSession) -> None:
    """Test getting a project by ID."""
    service = ProjectService(db_session)
    created = await service.create_project(
        ProjectCreate(
            name="Get Test",
            description="For getting",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
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
        ProjectCreate(
            name="Original",
            description="Original description",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
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
        ProjectCreate(
            name="Original",
            description="Keep this",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
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
    await service.create_project(
        ProjectCreate(
            name="Existing",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
    )
    created = await service.create_project(
        ProjectCreate(
            name="To Update",
            namespace="https://example.org/vocab2",
            identifier_prefix="UPD",
        )
    )

    with pytest.raises(ProjectNameExistsError):
        await service.update_project(created.id, ProjectUpdate(name="Existing"))


@pytest.mark.asyncio
async def test_delete_project(db_session: AsyncSession) -> None:
    """Test deleting a project."""
    service = ProjectService(db_session)
    created = await service.create_project(
        ProjectCreate(
            name="To Delete",
            namespace="https://example.org/vocab",
            identifier_prefix="TST",
        )
    )

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


# --- Identifier allocation ---


@pytest.mark.asyncio
async def test_allocate_identifier_sequential(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Successive allocations increment sequentially."""
    service = ProjectService(db_session)
    id1 = await service.allocate_identifier(project_with_prefix.id)
    id2 = await service.allocate_identifier(project_with_prefix.id)
    id3 = await service.allocate_identifier(project_with_prefix.id)
    assert id1 == "EVD000001"
    assert id2 == "EVD000002"
    assert id3 == "EVD000003"


@pytest.mark.asyncio
async def test_allocate_identifier_overflow(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Raises IdentifierAllocationError when counter reaches max."""
    project_with_prefix.identifier_counter = MAX_COUNTER
    await db_session.flush()

    service = ProjectService(db_session)
    with pytest.raises(IdentifierAllocationError, match="counter at maximum"):
        await service.allocate_identifier(project_with_prefix.id)


@pytest.mark.asyncio
async def test_allocate_identifier_missing_project_raises(db_session: AsyncSession) -> None:
    """Raises ProjectNotFoundError for nonexistent project."""
    service = ProjectService(db_session)
    fake_id = UUID("01234567-89ab-7def-8123-456789abcdef")
    with pytest.raises(ProjectNotFoundError):
        await service.allocate_identifier(fake_id)


# --- Counter reconciliation ---


@pytest.mark.asyncio
async def test_reconcile_advances_counter_and_is_monotonic(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Reconcile advances to highest match, then refuses to go backward."""
    service = ProjectService(db_session)
    await service.reconcile_identifier_counter(
        project_with_prefix.id, ["EVD000005", "EVD000003", "EVD000010"]
    )
    await db_session.refresh(project_with_prefix)
    assert project_with_prefix.identifier_counter == 10

    # Second reconcile with lower values must not regress
    await service.reconcile_identifier_counter(
        project_with_prefix.id, ["EVD000005"]
    )
    await db_session.refresh(project_with_prefix)
    assert project_with_prefix.identifier_counter == 10


@pytest.mark.asyncio
async def test_reconcile_skips_above_max(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Identifiers above MAX_COUNTER are ignored to prevent bricking."""
    service = ProjectService(db_session)
    await service.reconcile_identifier_counter(
        project_with_prefix.id, ["EVD1000000", "EVD000003"]
    )
    await db_session.refresh(project_with_prefix)
    assert project_with_prefix.identifier_counter == 3


@pytest.mark.asyncio
async def test_reconcile_ignores_non_matching_prefix(
    db_session: AsyncSession, project_with_prefix: Project
) -> None:
    """Identifiers with a different prefix are ignored."""
    service = ProjectService(db_session)
    await service.reconcile_identifier_counter(
        project_with_prefix.id, ["XYZ000010", "ABC000005"]
    )
    await db_session.refresh(project_with_prefix)
    assert project_with_prefix.identifier_counter == 0


@pytest.mark.asyncio
async def test_reconcile_no_prefix_is_noop(db_session: AsyncSession) -> None:
    """Reconcile on a project without prefix does nothing."""
    project = Project(
        name="No Prefix",
        namespace="https://example.org/np/",
        identifier_prefix="TST",
    )
    db_session.add(project)
    await db_session.flush()

    service = ProjectService(db_session)
    await service.reconcile_identifier_counter(project.id, ["EVD000010"])
    await db_session.refresh(project)
    assert project.identifier_counter == 0


@pytest.mark.asyncio
async def test_reconcile_missing_project_raises(db_session: AsyncSession) -> None:
    """Raises ProjectNotFoundError for nonexistent project."""
    service = ProjectService(db_session)
    fake_id = UUID("01234567-89ab-7def-8123-456789abcdef")
    with pytest.raises(ProjectNotFoundError):
        await service.reconcile_identifier_counter(fake_id, ["EVD000010"])
