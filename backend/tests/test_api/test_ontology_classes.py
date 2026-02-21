"""Tests for ontology class API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.models.project import Project


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(
        name="Test Project",
        namespace="https://example.org/vocab/",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def ontology_class_obj(db_session: AsyncSession, project: Project) -> OntologyClass:
    """Create an ontology class for testing."""
    ontology_class = OntologyClass(
        project_id=project.id,
        identifier="Reference",
        label="Reference",
        description="A bibliographic reference",
        scope_note="Used to represent source documents",
        uri="https://example.org/vocab/Reference",
    )
    db_session.add(ontology_class)
    await db_session.flush()
    await db_session.refresh(ontology_class)
    return ontology_class


class TestListOntologyClasses:
    """Tests for listing ontology classes."""

    @pytest.mark.asyncio
    async def test_list_ontology_classes_empty(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Test listing ontology classes when none exist."""
        response = await authenticated_client.get(f"/api/projects/{project.id}/classes")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_ontology_classes_returns_all(
        self,
        authenticated_client: AsyncClient,
        project: Project,
        ontology_class_obj: OntologyClass,
    ) -> None:
        """Test listing ontology classes returns all for project."""
        response = await authenticated_client.get(f"/api/projects/{project.id}/classes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(ontology_class_obj.id)
        assert data[0]["identifier"] == "Reference"

    @pytest.mark.asyncio
    async def test_list_ontology_classes_project_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test listing ontology classes for non-existent project."""
        response = await authenticated_client.get(f"/api/projects/{uuid4()}/classes")
        assert response.status_code == 404


class TestCreateOntologyClass:
    """Tests for creating ontology classes."""

    @pytest.mark.asyncio
    async def test_create_ontology_class(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Test creating an ontology class."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/classes",
            json={
                "identifier": "Outcome",
                "label": "Outcome",
                "description": "A research outcome",
                "scope_note": "Represents measured outcomes",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["identifier"] == "Outcome"
        assert data["label"] == "Outcome"
        assert data["description"] == "A research outcome"
        assert data["scope_note"] == "Represents measured outcomes"
        assert "id" in data
        assert "uri" in data
        assert data["uri"] == "https://example.org/vocab/Outcome"

    @pytest.mark.asyncio
    async def test_create_ontology_class_minimal(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Test creating an ontology class with only required fields."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/classes",
            json={
                "identifier": "Finding",
                "label": "Finding",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["identifier"] == "Finding"
        assert data["description"] is None
        assert data["scope_note"] is None

    @pytest.mark.asyncio
    async def test_create_ontology_class_duplicate_identifier(
        self,
        authenticated_client: AsyncClient,
        project: Project,
        ontology_class_obj: OntologyClass,
    ) -> None:
        """Test creating an ontology class with duplicate identifier."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/classes",
            json={
                "identifier": "Reference",  # Same as ontology_class_obj
                "label": "Another Reference",
            },
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_ontology_class_project_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test creating an ontology class for non-existent project."""
        response = await authenticated_client.post(
            f"/api/projects/{uuid4()}/classes",
            json={
                "identifier": "TestClass",
                "label": "Test",
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_ontology_class_invalid_identifier(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Test creating an ontology class with invalid identifier."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/classes",
            json={
                "identifier": "123invalid",
                "label": "Invalid",
            },
        )
        assert response.status_code == 422


class TestGetOntologyClass:
    """Tests for getting a single ontology class."""

    @pytest.mark.asyncio
    async def test_get_ontology_class(
        self, authenticated_client: AsyncClient, ontology_class_obj: OntologyClass
    ) -> None:
        """Test getting a single ontology class."""
        response = await authenticated_client.get(f"/api/classes/{ontology_class_obj.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(ontology_class_obj.id)
        assert data["identifier"] == "Reference"
        assert data["label"] == "Reference"
        assert data["description"] == "A bibliographic reference"
        assert data["scope_note"] == "Used to represent source documents"

    @pytest.mark.asyncio
    async def test_get_ontology_class_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test getting a non-existent ontology class."""
        response = await authenticated_client.get(f"/api/classes/{uuid4()}")
        assert response.status_code == 404


class TestUpdateOntologyClass:
    """Tests for updating ontology classes."""

    @pytest.mark.asyncio
    async def test_update_ontology_class_label(
        self, authenticated_client: AsyncClient, ontology_class_obj: OntologyClass
    ) -> None:
        """Test updating an ontology class's label."""
        response = await authenticated_client.put(
            f"/api/classes/{ontology_class_obj.id}",
            json={"label": "Updated Reference"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Updated Reference"
        assert data["identifier"] == "Reference"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_ontology_class_description(
        self, authenticated_client: AsyncClient, ontology_class_obj: OntologyClass
    ) -> None:
        """Test updating an ontology class's description."""
        response = await authenticated_client.put(
            f"/api/classes/{ontology_class_obj.id}",
            json={"description": "New description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_update_ontology_class_scope_note(
        self, authenticated_client: AsyncClient, ontology_class_obj: OntologyClass
    ) -> None:
        """Test updating an ontology class's scope note."""
        response = await authenticated_client.put(
            f"/api/classes/{ontology_class_obj.id}",
            json={"scope_note": "Updated scope note"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scope_note"] == "Updated scope note"

    @pytest.mark.asyncio
    async def test_update_ontology_class_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test updating a non-existent ontology class."""
        response = await authenticated_client.put(
            f"/api/classes/{uuid4()}",
            json={"label": "New Label"},
        )
        assert response.status_code == 404


class TestDeleteOntologyClass:
    """Tests for deleting ontology classes."""

    @pytest.mark.asyncio
    async def test_delete_ontology_class(
        self, authenticated_client: AsyncClient, ontology_class_obj: OntologyClass
    ) -> None:
        """Test deleting an ontology class."""
        response = await authenticated_client.delete(
            f"/api/classes/{ontology_class_obj.id}"
        )
        assert response.status_code == 204

        # Verify it's gone
        response = await authenticated_client.get(f"/api/classes/{ontology_class_obj.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_ontology_class_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test deleting a non-existent ontology class."""
        response = await authenticated_client.delete(f"/api/classes/{uuid4()}")
        assert response.status_code == 404


class TestOntologyClassURICollision:
    """Tests for URI collision returning 409."""

    @pytest.mark.asyncio
    async def test_duplicate_uri_returns_409(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Two classes with same explicit URI but different identifiers → 409."""
        response1 = await authenticated_client.post(
            f"/api/projects/{project.id}/classes",
            json={
                "identifier": "ClassA",
                "label": "Class A",
                "uri": "https://example.org/vocab/sharedUri",
            },
        )
        assert response1.status_code == 201

        response2 = await authenticated_client.post(
            f"/api/projects/{project.id}/classes",
            json={
                "identifier": "ClassB",
                "label": "Class B",
                "uri": "https://example.org/vocab/sharedUri",
            },
        )
        assert response2.status_code == 409
