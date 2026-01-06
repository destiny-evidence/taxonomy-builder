"""Integration tests that verify data persistence across requests.

These tests use the real database session manager (with commit/rollback)
to ensure data actually persists, unlike unit tests which use
transaction rollback for isolation.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from taxonomy_builder.database import db_manager
from taxonomy_builder.main import app


async def _clean_tables() -> None:
    """Delete all data from tables (preserves schema)."""
    async with db_manager.engine.begin() as conn:
        # Delete in order to respect foreign key constraints
        await conn.execute(text("DELETE FROM concept_broader"))
        await conn.execute(text("DELETE FROM concepts"))
        await conn.execute(text("DELETE FROM concept_schemes"))
        await conn.execute(text("DELETE FROM projects"))


@pytest.fixture
async def integration_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide a client that tests the REAL get_db implementation.

    Does NOT override get_db, so we test the actual commit/rollback behavior.
    Uses db_manager already initialized by conftest session fixture.
    """
    # Clean any existing data before tests
    await _clean_tables()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    # Clean up after tests
    await _clean_tables()


class TestDataPersistence:
    """Tests that verify data persists across separate requests."""

    async def test_created_project_can_be_retrieved(self, integration_client: AsyncClient):
        """Creating a project in one request should be retrievable in another."""
        # Create a project
        create_response = await integration_client.post(
            "/api/projects",
            json={"name": "Persistence Test", "description": "Testing data persistence"},
        )
        assert create_response.status_code == 201
        created = create_response.json()

        # Retrieve it in a separate request
        get_response = await integration_client.get(f"/api/projects/{created['id']}")
        assert get_response.status_code == 200
        retrieved = get_response.json()

        assert retrieved["name"] == "Persistence Test"
        assert retrieved["description"] == "Testing data persistence"

    async def test_created_project_appears_in_list(self, integration_client: AsyncClient):
        """Created project should appear in the project list."""
        # Create a project
        create_response = await integration_client.post(
            "/api/projects",
            json={"name": "List Test Project"},
        )
        assert create_response.status_code == 201

        # List all projects
        list_response = await integration_client.get("/api/projects")
        assert list_response.status_code == 200
        projects = list_response.json()

        assert any(p["name"] == "List Test Project" for p in projects)

    async def test_updated_project_persists(self, integration_client: AsyncClient):
        """Updated project data should persist across requests."""
        # Create
        create_response = await integration_client.post(
            "/api/projects",
            json={"name": "Update Test"},
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Update
        update_response = await integration_client.put(
            f"/api/projects/{project_id}",
            json={"name": "Updated Name"},
        )
        assert update_response.status_code == 200

        # Retrieve and verify
        get_response = await integration_client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Updated Name"

    async def test_deleted_project_is_gone(self, integration_client: AsyncClient):
        """Deleted project should not be retrievable."""
        # Create
        create_response = await integration_client.post(
            "/api/projects",
            json={"name": "Delete Test"},
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Delete
        delete_response = await integration_client.delete(f"/api/projects/{project_id}")
        assert delete_response.status_code == 204

        # Verify gone
        get_response = await integration_client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 404

    async def test_scheme_persists_under_project(self, integration_client: AsyncClient):
        """Created scheme should persist and be retrievable."""
        # Create project
        project_response = await integration_client.post(
            "/api/projects",
            json={"name": "Scheme Test Project"},
        )
        project_id = project_response.json()["id"]

        # Create scheme
        scheme_response = await integration_client.post(
            f"/api/projects/{project_id}/schemes",
            json={"title": "Test Scheme"},
        )
        assert scheme_response.status_code == 201
        scheme_id = scheme_response.json()["id"]

        # Retrieve scheme
        get_response = await integration_client.get(f"/api/schemes/{scheme_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Test Scheme"

    async def test_concept_persists_under_scheme(self, integration_client: AsyncClient):
        """Created concept should persist and be retrievable."""
        # Create project
        project_response = await integration_client.post(
            "/api/projects",
            json={"name": "Concept Test Project"},
        )
        project_id = project_response.json()["id"]

        # Create scheme
        scheme_response = await integration_client.post(
            f"/api/projects/{project_id}/schemes",
            json={"title": "Concept Test Scheme"},
        )
        scheme_id = scheme_response.json()["id"]

        # Create concept
        concept_response = await integration_client.post(
            f"/api/schemes/{scheme_id}/concepts",
            json={"pref_label": "Test Concept"},
        )
        assert concept_response.status_code == 201
        concept_id = concept_response.json()["id"]

        # Retrieve concept
        get_response = await integration_client.get(f"/api/concepts/{concept_id}")
        assert get_response.status_code == 200
        assert get_response.json()["pref_label"] == "Test Concept"

    async def test_broader_relationship_persists(self, integration_client: AsyncClient):
        """Broader relationships should persist across requests."""
        # Create project and scheme
        project_response = await integration_client.post(
            "/api/projects",
            json={"name": "Broader Test Project"},
        )
        project_id = project_response.json()["id"]

        scheme_response = await integration_client.post(
            f"/api/projects/{project_id}/schemes",
            json={"title": "Broader Test Scheme"},
        )
        scheme_id = scheme_response.json()["id"]

        # Create parent concept
        parent_response = await integration_client.post(
            f"/api/schemes/{scheme_id}/concepts",
            json={"pref_label": "Parent Concept"},
        )
        parent_id = parent_response.json()["id"]

        # Create child concept
        child_response = await integration_client.post(
            f"/api/schemes/{scheme_id}/concepts",
            json={"pref_label": "Child Concept"},
        )
        child_id = child_response.json()["id"]

        # Add broader relationship
        broader_response = await integration_client.post(
            f"/api/concepts/{child_id}/broader",
            json={"broader_concept_id": parent_id},
        )
        assert broader_response.status_code == 201

        # Retrieve child and verify broader relationship persisted
        get_response = await integration_client.get(f"/api/concepts/{child_id}")
        assert get_response.status_code == 200
        child = get_response.json()
        assert len(child["broader"]) == 1
        assert child["broader"][0]["id"] == parent_id
