"""Tests for the Projects API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient) -> None:
    """Test listing projects when none exist."""
    response = await client.get("/api/projects")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test listing projects."""
    # Create some projects directly in the database
    project1 = Project(name="Project 1", description="First project")
    project2 = Project(name="Project 2", description="Second project")
    db_session.add_all([project1, project2])
    await db_session.flush()

    response = await client.get("/api/projects")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    names = {p["name"] for p in data}
    assert names == {"Project 1", "Project 2"}


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient) -> None:
    """Test creating a new project."""
    response = await client.post(
        "/api/projects",
        json={"name": "New Project", "description": "A new project"},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "New Project"
    assert data["description"] == "A new project"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_project_without_description(client: AsyncClient) -> None:
    """Test creating a project without a description."""
    response = await client.post("/api/projects", json={"name": "No Description Project"})
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "No Description Project"
    assert data["description"] is None


@pytest.mark.asyncio
async def test_create_project_duplicate_name(client: AsyncClient) -> None:
    """Test creating a project with a duplicate name fails."""
    # Create first project
    response1 = await client.post("/api/projects", json={"name": "Duplicate Name"})
    assert response1.status_code == 201

    # Try to create second project with same name
    response2 = await client.post("/api/projects", json={"name": "Duplicate Name"})
    assert response2.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_create_project_empty_name(client: AsyncClient) -> None:
    """Test creating a project with empty name fails."""
    response = await client.post("/api/projects", json={"name": ""})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test getting a single project by ID."""
    project = Project(name="Get Test", description="For getting")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    response = await client.get(f"/api/projects/{project.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(project.id)
    assert data["name"] == "Get Test"
    assert data["description"] == "For getting"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent project returns 404."""
    response = await client.get("/api/projects/01234567-89ab-7def-8123-456789abcdef")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_invalid_uuid(client: AsyncClient) -> None:
    """Test getting a project with invalid UUID returns 422."""
    response = await client.get("/api/projects/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test updating a project."""
    project = Project(name="Original", description="Original description")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    response = await client.put(
        f"/api/projects/{project.id}",
        json={"name": "Updated", "description": "Updated description"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_project_partial(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test partially updating a project (only name)."""
    project = Project(name="Original", description="Keep this")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    response = await client.put(f"/api/projects/{project.id}", json={"name": "New Name"})
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Keep this"


@pytest.mark.asyncio
async def test_update_project_not_found(client: AsyncClient) -> None:
    """Test updating a non-existent project returns 404."""
    response = await client.put(
        "/api/projects/01234567-89ab-7def-8123-456789abcdef", json={"name": "New Name"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test deleting a project."""
    project = Project(name="To Delete", description="Will be deleted")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    response = await client.delete(f"/api/projects/{project.id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/projects/{project.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(client: AsyncClient) -> None:
    """Test deleting a non-existent project returns 404."""
    response = await client.delete("/api/projects/01234567-89ab-7def-8123-456789abcdef")
    assert response.status_code == 404
