"""Tests for ConceptScheme API endpoints."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.main import app
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from tests.factories import ConceptSchemeFactory, ProjectFactory, PropertyFactory, flush


@pytest.fixture
async def project(db_session: AsyncSession):
    """Create a project for testing."""
    return await flush(db_session, ProjectFactory.create(name="Test Project", description="For testing schemes"))


@pytest.fixture
async def scheme(db_session: AsyncSession, project):
    """Create a concept scheme for testing."""
    return await flush(db_session, ConceptSchemeFactory.create(project=project, title="Test Scheme", description="A test scheme", uri="http://example.org/schemes/test"))


# List schemes tests


@pytest.mark.asyncio
async def test_list_schemes_empty(authenticated_client: AsyncClient, project: Project) -> None:
    """Test listing schemes when none exist."""
    response = await authenticated_client.get(f"/api/projects/{project.id}/schemes")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_schemes(authenticated_client: AsyncClient, project: Project, scheme: ConceptScheme) -> None:
    """Test listing schemes returns all schemes for project."""
    response = await authenticated_client.get(f"/api/projects/{project.id}/schemes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(scheme.id)
    assert data[0]["title"] == "Test Scheme"


@pytest.mark.asyncio
async def test_list_schemes_project_not_found(authenticated_client: AsyncClient) -> None:
    """Test listing schemes for non-existent project."""
    response = await authenticated_client.get(f"/api/projects/{uuid4()}/schemes")
    assert response.status_code == 404


# Create scheme tests


@pytest.mark.asyncio
async def test_create_scheme(authenticated_client: AsyncClient, project: Project) -> None:
    """Test creating a new scheme."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/schemes",
        json={
            "title": "New Scheme",
            "description": "A new scheme",
            "uri": "http://example.org/new",
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
async def test_create_scheme_title_only(authenticated_client: AsyncClient, project: Project) -> None:
    """Test creating a scheme with only title."""
    response = await authenticated_client.post(
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
    authenticated_client: AsyncClient, project: Project, scheme: ConceptScheme
) -> None:
    """Test creating a scheme with duplicate title fails."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/schemes",
        json={"title": "Test Scheme"},  # Same as existing scheme
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_scheme_empty_title(authenticated_client: AsyncClient, project: Project) -> None:
    """Test creating a scheme with empty title fails."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/schemes",
        json={"title": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_scheme_project_not_found(authenticated_client: AsyncClient) -> None:
    """Test creating a scheme for non-existent project."""
    response = await authenticated_client.post(
        f"/api/projects/{uuid4()}/schemes",
        json={"title": "New Scheme"},
    )
    assert response.status_code == 404


# Get scheme tests


@pytest.mark.asyncio
async def test_get_scheme(authenticated_client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test getting a single scheme."""
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(scheme.id)
    assert data["title"] == "Test Scheme"
    assert data["description"] == "A test scheme"


@pytest.mark.asyncio
async def test_get_scheme_not_found(authenticated_client: AsyncClient) -> None:
    """Test getting a non-existent scheme."""
    response = await authenticated_client.get(f"/api/schemes/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_scheme_invalid_uuid(authenticated_client: AsyncClient) -> None:
    """Test getting a scheme with invalid UUID."""
    response = await authenticated_client.get("/api/schemes/not-a-uuid")
    assert response.status_code == 422


# Update scheme tests


@pytest.mark.asyncio
async def test_update_scheme(authenticated_client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test updating a scheme."""
    response = await authenticated_client.put(
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
async def test_update_scheme_partial(authenticated_client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test partial update of a scheme."""
    response = await authenticated_client.put(
        f"/api/schemes/{scheme.id}",
        json={"description": "Only description changed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Scheme"  # Unchanged
    assert data["description"] == "Only description changed"


@pytest.mark.asyncio
async def test_update_scheme_not_found(authenticated_client: AsyncClient) -> None:
    """Test updating a non-existent scheme."""
    response = await authenticated_client.put(
        f"/api/schemes/{uuid4()}",
        json={"title": "New Title"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_scheme_duplicate_title(
    authenticated_client: AsyncClient, db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test updating scheme to duplicate title fails."""
    # Create another scheme
    scheme2 = ConceptSchemeFactory.create(project=project, title="Another Scheme")
    await db_session.flush()

    # Try to rename it to the same title as the first scheme
    response = await authenticated_client.put(
        f"/api/schemes/{scheme2.id}",
        json={"title": "Test Scheme"},
    )
    assert response.status_code == 409


# Delete scheme tests


@pytest.mark.asyncio
async def test_delete_scheme(authenticated_client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test deleting a scheme."""
    response = await authenticated_client.delete(f"/api/schemes/{scheme.id}")
    assert response.status_code == 204

    # Verify it's deleted
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_scheme_not_found(authenticated_client: AsyncClient) -> None:
    """Test deleting a non-existent scheme."""
    response = await authenticated_client.delete(f"/api/schemes/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_scheme_referenced_by_property(
    authenticated_client: AsyncClient, db_session: AsyncSession, project: Project, scheme: ConceptScheme
) -> None:
    """Test deleting a scheme that is referenced by a property fails."""
    # Create a property that references this scheme
    PropertyFactory.create(project=project, identifier="testProp", label="Test Property", domain_class="https://evrepo.example.org/vocab/Finding", range_scheme=scheme, cardinality="single", required=False)
    await db_session.flush()

    # Try to delete the scheme
    response = await authenticated_client.delete(f"/api/schemes/{scheme.id}")
    assert response.status_code == 409
    assert "referenced by" in response.json()["detail"].lower()
