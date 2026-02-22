"""Tests for Property API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property


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
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a concept scheme for testing."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Education Level",
        uri="http://example.org/schemes/education-level",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.fixture
async def property_obj(db_session: AsyncSession, project: Project) -> Property:
    """Create a property for testing."""
    prop = Property(
        project_id=project.id,
        identifier="sampleSize",
        label="Sample Size",
        description="The sample size",
        domain_class="https://evrepo.example.org/vocab/Finding",
        range_datatype="xsd:integer",
        cardinality="single",
        required=True,
    )
    db_session.add(prop)
    await db_session.flush()
    await db_session.refresh(prop)
    return prop


class TestListProperties:
    """Tests for listing properties."""

    @pytest.mark.asyncio
    async def test_list_properties_empty(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Test listing properties when none exist."""
        response = await authenticated_client.get(f"/api/projects/{project.id}/properties")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_properties_returns_all(
        self, authenticated_client: AsyncClient, project: Project, property_obj: Property
    ) -> None:
        """Test listing properties returns all for project."""
        response = await authenticated_client.get(f"/api/projects/{project.id}/properties")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(property_obj.id)
        assert data[0]["identifier"] == "sampleSize"

    @pytest.mark.asyncio
    async def test_list_properties_project_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test listing properties for non-existent project."""
        response = await authenticated_client.get(f"/api/projects/{uuid4()}/properties")
        assert response.status_code == 404


class TestCreateProperty:
    """Tests for creating properties."""

    @pytest.mark.asyncio
    async def test_create_property_with_datatype(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Test creating a property with range_datatype."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/properties",
            json={
                "identifier": "sampleSize",
                "label": "Sample Size",
                "domain_class": "https://evrepo.example.org/vocab/Finding",
                "range_datatype": "xsd:integer",
                "cardinality": "single",
                "required": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["identifier"] == "sampleSize"
        assert data["label"] == "Sample Size"
        assert data["range_datatype"] == "xsd:integer"
        assert data["range_scheme_id"] is None
        assert data["required"] is True
        assert "id" in data
        assert "uri" in data

    @pytest.mark.asyncio
    async def test_create_property_with_scheme(
        self, authenticated_client: AsyncClient, project: Project, scheme: ConceptScheme
    ) -> None:
        """Test creating a property with range_scheme_id."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/properties",
            json={
                "identifier": "educationLevel",
                "label": "Education Level",
                "domain_class": "https://evrepo.example.org/vocab/Finding",
                "range_scheme_id": str(scheme.id),
                "cardinality": "multiple",
                "required": False,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["identifier"] == "educationLevel"
        assert data["range_scheme_id"] == str(scheme.id)
        assert data["range_datatype"] is None

    @pytest.mark.asyncio
    async def test_create_property_invalid_domain_class(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Test creating a property with invalid domain class."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/properties",
            json={
                "identifier": "testProp",
                "label": "Test",
                "domain_class": "https://invalid.org/NotAClass",
                "range_datatype": "xsd:string",
                "cardinality": "single",
            },
        )
        assert response.status_code == 400
        assert "domain class" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_property_with_range_class(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Test creating a property with range_class (URI string)."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/properties",
            json={
                "identifier": "educationLevel",
                "label": "Education Level",
                "domain_class": "https://evrepo.example.org/vocab/Finding",
                "range_class": "https://example.org/ontology/EducationLevel",
                "cardinality": "single",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["range_class"] == "https://example.org/ontology/EducationLevel"
        assert data["range_scheme_id"] is None
        assert data["range_datatype"] is None

    @pytest.mark.asyncio
    async def test_create_property_invalid_range(
        self, authenticated_client: AsyncClient, project: Project
    ) -> None:
        """Test creating a property with no range field — schema rejects with 422."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/properties",
            json={
                "identifier": "testProp",
                "label": "Test",
                "domain_class": "https://evrepo.example.org/vocab/Finding",
                "cardinality": "single",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_property_duplicate_identifier(
        self, authenticated_client: AsyncClient, project: Project, property_obj: Property
    ) -> None:
        """Test creating a property with duplicate identifier."""
        response = await authenticated_client.post(
            f"/api/projects/{project.id}/properties",
            json={
                "identifier": "sampleSize",  # Same as property_obj
                "label": "Another Sample Size",
                "domain_class": "https://evrepo.example.org/vocab/Finding",
                "range_datatype": "xsd:integer",
                "cardinality": "single",
            },
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_property_project_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test creating a property for non-existent project."""
        response = await authenticated_client.post(
            f"/api/projects/{uuid4()}/properties",
            json={
                "identifier": "testProp",
                "label": "Test",
                "domain_class": "https://evrepo.example.org/vocab/Finding",
                "range_datatype": "xsd:string",
                "cardinality": "single",
            },
        )
        assert response.status_code == 404


class TestGetProperty:
    """Tests for getting a single property."""

    @pytest.mark.asyncio
    async def test_get_property(
        self, authenticated_client: AsyncClient, property_obj: Property
    ) -> None:
        """Test getting a single property."""
        response = await authenticated_client.get(f"/api/properties/{property_obj.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(property_obj.id)
        assert data["identifier"] == "sampleSize"

    @pytest.mark.asyncio
    async def test_get_property_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test getting a non-existent property."""
        response = await authenticated_client.get(f"/api/properties/{uuid4()}")
        assert response.status_code == 404


class TestUpdateProperty:
    """Tests for updating properties."""

    @pytest.mark.asyncio
    async def test_update_property_label(
        self, authenticated_client: AsyncClient, property_obj: Property
    ) -> None:
        """Test updating a property's label."""
        response = await authenticated_client.put(
            f"/api/properties/{property_obj.id}",
            json={"label": "Updated Sample Size"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Updated Sample Size"
        assert data["identifier"] == "sampleSize"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_property_description(
        self, authenticated_client: AsyncClient, property_obj: Property
    ) -> None:
        """Test updating a property's description."""
        response = await authenticated_client.put(
            f"/api/properties/{property_obj.id}",
            json={"description": "New description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_update_property_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test updating a non-existent property."""
        response = await authenticated_client.put(
            f"/api/properties/{uuid4()}",
            json={"label": "New Label"},
        )
        assert response.status_code == 404


class TestDeleteProperty:
    """Tests for deleting properties."""

    @pytest.mark.asyncio
    async def test_delete_property(
        self, authenticated_client: AsyncClient, property_obj: Property
    ) -> None:
        """Test deleting a property."""
        response = await authenticated_client.delete(f"/api/properties/{property_obj.id}")
        assert response.status_code == 204

        # Verify it's gone
        response = await authenticated_client.get(f"/api/properties/{property_obj.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_property_not_found(
        self, authenticated_client: AsyncClient
    ) -> None:
        """Test deleting a non-existent property."""
        response = await authenticated_client.delete(f"/api/properties/{uuid4()}")
        assert response.status_code == 404
