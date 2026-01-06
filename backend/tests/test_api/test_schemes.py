"""Tests for ConceptScheme API endpoints."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.main import app
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


@pytest.fixture
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a concept scheme for testing."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        description="A test scheme",
        uri="http://example.org/schemes/test",
        publisher="Test Publisher",
        version="1.0",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


# List schemes tests


@pytest.mark.asyncio
async def test_list_schemes_empty(client: AsyncClient, project: Project) -> None:
    """Test listing schemes when none exist."""
    response = await client.get(f"/api/projects/{project.id}/schemes")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_schemes(client: AsyncClient, project: Project, scheme: ConceptScheme) -> None:
    """Test listing schemes returns all schemes for project."""
    response = await client.get(f"/api/projects/{project.id}/schemes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(scheme.id)
    assert data[0]["title"] == "Test Scheme"


@pytest.mark.asyncio
async def test_list_schemes_project_not_found(client: AsyncClient) -> None:
    """Test listing schemes for non-existent project."""
    response = await client.get(f"/api/projects/{uuid4()}/schemes")
    assert response.status_code == 404


# Create scheme tests


@pytest.mark.asyncio
async def test_create_scheme(client: AsyncClient, project: Project) -> None:
    """Test creating a new scheme."""
    response = await client.post(
        f"/api/projects/{project.id}/schemes",
        json={
            "title": "New Scheme",
            "description": "A new scheme",
            "uri": "http://example.org/new",
            "publisher": "Publisher",
            "version": "1.0",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Scheme"
    assert data["description"] == "A new scheme"
    assert data["uri"] == "http://example.org/new"
    assert data["project_id"] == str(project.id)
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_scheme_title_only(client: AsyncClient, project: Project) -> None:
    """Test creating a scheme with only title."""
    response = await client.post(
        f"/api/projects/{project.id}/schemes",
        json={"title": "Minimal Scheme"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal Scheme"
    assert data["description"] is None
    assert data["uri"] is None


@pytest.mark.asyncio
async def test_create_scheme_duplicate_title(
    client: AsyncClient, project: Project, scheme: ConceptScheme
) -> None:
    """Test creating a scheme with duplicate title fails."""
    response = await client.post(
        f"/api/projects/{project.id}/schemes",
        json={"title": "Test Scheme"},  # Same as existing scheme
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_scheme_empty_title(client: AsyncClient, project: Project) -> None:
    """Test creating a scheme with empty title fails."""
    response = await client.post(
        f"/api/projects/{project.id}/schemes",
        json={"title": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_scheme_project_not_found(client: AsyncClient) -> None:
    """Test creating a scheme for non-existent project."""
    response = await client.post(
        f"/api/projects/{uuid4()}/schemes",
        json={"title": "New Scheme"},
    )
    assert response.status_code == 404


# Get scheme tests


@pytest.mark.asyncio
async def test_get_scheme(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test getting a single scheme."""
    response = await client.get(f"/api/schemes/{scheme.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(scheme.id)
    assert data["title"] == "Test Scheme"
    assert data["description"] == "A test scheme"


@pytest.mark.asyncio
async def test_get_scheme_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent scheme."""
    response = await client.get(f"/api/schemes/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_scheme_invalid_uuid(client: AsyncClient) -> None:
    """Test getting a scheme with invalid UUID."""
    response = await client.get("/api/schemes/not-a-uuid")
    assert response.status_code == 422


# Update scheme tests


@pytest.mark.asyncio
async def test_update_scheme(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test updating a scheme."""
    response = await client.put(
        f"/api/schemes/{scheme.id}",
        json={
            "title": "Updated Scheme",
            "description": "Updated description",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Scheme"
    assert data["description"] == "Updated description"
    # Other fields should remain unchanged
    assert data["uri"] == "http://example.org/schemes/test"


@pytest.mark.asyncio
async def test_update_scheme_partial(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test partial update of a scheme."""
    response = await client.put(
        f"/api/schemes/{scheme.id}",
        json={"description": "Only description changed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Scheme"  # Unchanged
    assert data["description"] == "Only description changed"


@pytest.mark.asyncio
async def test_update_scheme_not_found(client: AsyncClient) -> None:
    """Test updating a non-existent scheme."""
    response = await client.put(
        f"/api/schemes/{uuid4()}",
        json={"title": "New Title"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_scheme_duplicate_title(
    client: AsyncClient, db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test updating scheme to duplicate title fails."""
    # Create another scheme
    scheme2 = ConceptScheme(project_id=project.id, title="Another Scheme")
    db_session.add(scheme2)
    await db_session.flush()

    # Try to rename it to the same title as the first scheme
    response = await client.put(
        f"/api/schemes/{scheme2.id}",
        json={"title": "Test Scheme"},
    )
    assert response.status_code == 409


# Delete scheme tests


@pytest.mark.asyncio
async def test_delete_scheme(client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test deleting a scheme."""
    response = await client.delete(f"/api/schemes/{scheme.id}")
    assert response.status_code == 204

    # Verify it's deleted
    response = await client.get(f"/api/schemes/{scheme.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_scheme_not_found(client: AsyncClient) -> None:
    """Test deleting a non-existent scheme."""
    response = await client.delete(f"/api/schemes/{uuid4()}")
    assert response.status_code == 404
