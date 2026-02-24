"""Tests for the Projects API endpoints."""

from datetime import datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.schemas.snapshot import (
    SnapshotClass,
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotProperty,
    SnapshotScheme,
    SnapshotVocabulary,
)


@pytest.fixture
async def published_version(db_session: AsyncSession) -> PublishedVersion:
    """Create a project with a published version containing a snapshot."""
    project = Project(name="Export Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    animal_id = uuid4()
    mammal_id = uuid4()
    scheme_id = uuid4()

    snapshot = SnapshotVocabulary(
        project=SnapshotProjectMetadata(
            id=project.id,
            name=project.name,
            namespace="http://example.org/namespace"
        ),
        concept_schemes=[
            SnapshotScheme(
                id=scheme_id,
                title="Test Taxonomy",
                description="A test taxonomy",
                uri="http://example.org/taxonomy",
                concepts=[
                    SnapshotConcept(
                        id=animal_id,
                        pref_label="Animals",
                        identifier="animals",
                        uri="http://example.org/taxonomy/animals",
                        definition="Living organisms",
                    ),
                    SnapshotConcept(
                        id=mammal_id,
                        pref_label="Mammals",
                        identifier="mammals",
                        uri="http://example.org/taxonomy/mammals",
                        broader_ids=[animal_id],
                    ),
                ],
            )
        ],
        properties=[
            SnapshotProperty(
                id=uuid4(),
                identifier="studyType",
                label="Study Type",
                uri="http://example.org/ontology/studyType",
                domain_class="http://example.org/ontology/Study",
                range_scheme_id=scheme_id,
                range_scheme_uri="http://example.org/taxonomy",
                cardinality="single",
                required=True,
            ),
        ],
        classes=[
            SnapshotClass(
                id=uuid4(),
                identifier="Study",
                label="Study",
                uri="http://example.org/ontology/Study",
                description="A research study",
            ),
        ],
    )

    published = PublishedVersion(
        project_id=project.id,
        version="1.0",
        title="v1.0",
        snapshot=snapshot.model_dump(mode="json"),
        published_at=datetime.now()
    )
    db_session.add(published)
    await db_session.flush()
    await db_session.refresh(published)
    return published


@pytest.mark.asyncio
async def test_list_projects_empty(authenticated_client: AsyncClient) -> None:
    """Test listing projects when none exist."""
    response = await authenticated_client.get("/api/projects")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_projects(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test listing projects."""
    # Create some projects directly in the database
    project1 = Project(name="Project 1", description="First project")
    project2 = Project(name="Project 2", description="Second project")
    db_session.add_all([project1, project2])
    await db_session.flush()

    response = await authenticated_client.get("/api/projects")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    names = {p["name"] for p in data}
    assert names == {"Project 1", "Project 2"}


@pytest.mark.asyncio
async def test_create_project(authenticated_client: AsyncClient) -> None:
    """Test creating a new project."""
    response = await authenticated_client.post(
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
async def test_create_project_without_description(authenticated_client: AsyncClient) -> None:
    """Test creating a project without a description."""
    response = await authenticated_client.post("/api/projects", json={"name": "No Description Project"})
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "No Description Project"
    assert data["description"] is None


@pytest.mark.asyncio
async def test_create_project_duplicate_name(authenticated_client: AsyncClient) -> None:
    """Test creating a project with a duplicate name fails."""
    # Create first project
    response1 = await authenticated_client.post("/api/projects", json={"name": "Duplicate Name"})
    assert response1.status_code == 201

    # Try to create second project with same name
    response2 = await authenticated_client.post("/api/projects", json={"name": "Duplicate Name"})
    assert response2.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_create_project_empty_name(authenticated_client: AsyncClient) -> None:
    """Test creating a project with empty name fails."""
    response = await authenticated_client.post("/api/projects", json={"name": ""})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_project(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test getting a single project by ID."""
    project = Project(name="Get Test", description="For getting")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    response = await authenticated_client.get(f"/api/projects/{project.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(project.id)
    assert data["name"] == "Get Test"
    assert data["description"] == "For getting"


@pytest.mark.asyncio
async def test_get_project_not_found(authenticated_client: AsyncClient) -> None:
    """Test getting a non-existent project returns 404."""
    response = await authenticated_client.get("/api/projects/01234567-89ab-7def-8123-456789abcdef")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_invalid_uuid(authenticated_client: AsyncClient) -> None:
    """Test getting a project with invalid UUID returns 422."""
    response = await authenticated_client.get("/api/projects/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_project(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test updating a project."""
    project = Project(name="Original", description="Original description")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    response = await authenticated_client.put(
        f"/api/projects/{project.id}",
        json={"name": "Updated", "description": "Updated description"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_project_partial(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test partially updating a project (only name)."""
    project = Project(name="Original", description="Keep this")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    response = await authenticated_client.put(f"/api/projects/{project.id}", json={"name": "New Name"})
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Keep this"


@pytest.mark.asyncio
async def test_update_project_not_found(authenticated_client: AsyncClient) -> None:
    """Test updating a non-existent project returns 404."""
    response = await authenticated_client.put(
        "/api/projects/01234567-89ab-7def-8123-456789abcdef", json={"name": "New Name"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test deleting a project."""
    project = Project(name="To Delete", description="Will be deleted")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    response = await authenticated_client.delete(f"/api/projects/{project.id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await authenticated_client.get(f"/api/projects/{project.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(authenticated_client: AsyncClient) -> None:
    """Test deleting a non-existent project returns 404."""
    response = await authenticated_client.delete("/api/projects/01234567-89ab-7def-8123-456789abcdef")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_project_with_namespace(authenticated_client: AsyncClient) -> None:
    """Test creating a project with a namespace."""
    response = await authenticated_client.post(
        "/api/projects",
        json={
            "name": "ESEA Vocabulary",
            "description": "Education vocabulary",
            "namespace": "https://esea.org/vocab",
        },
    )
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "ESEA Vocabulary"
    assert data["namespace"] == "https://esea.org/vocab"


@pytest.mark.asyncio
async def test_create_project_with_namespace_stored_in_db(
    authenticated_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that namespace is persisted to database."""
    response = await authenticated_client.post(
        "/api/projects",
        json={
            "name": "Test Project",
            "namespace": "https://example.org/vocab",
        },
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Verify it's in the database
    get_response = await authenticated_client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["namespace"] == "https://example.org/vocab"


@pytest.mark.asyncio
async def test_create_project_with_invalid_namespace(authenticated_client: AsyncClient) -> None:
    """Test that creating a project with an invalid namespace URI fails."""
    response = await authenticated_client.post(
        "/api/projects",
        json={
            "name": "Invalid Namespace Project",
            "namespace": "not-a-valid-uri",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_with_malformed_namespace(authenticated_client: AsyncClient) -> None:
    """Test that creating a project with a malformed namespace URI fails."""
    response = await authenticated_client.post(
        "/api/projects",
        json={
            "name": "Malformed Namespace Project",
            "namespace": "ht!tp://bad-url",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_with_http_namespace(authenticated_client: AsyncClient) -> None:
    """Test that http:// namespaces are accepted (not just https://)."""
    response = await authenticated_client.post(
        "/api/projects",
        json={
            "name": "HTTP Namespace Project",
            "namespace": "http://example.org/vocab",
        },
    )
    assert response.status_code == 201
    assert response.json()["namespace"] == "http://example.org/vocab"


@pytest.mark.asyncio
async def test_update_project_add_namespace(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test adding a namespace to an existing project."""
    # Create project without namespace
    project = Project(name="No Namespace", description="Project without namespace")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    # Add namespace via update
    response = await authenticated_client.put(
        f"/api/projects/{project.id}",
        json={"namespace": "https://example.org/new-vocab"},
    )
    assert response.status_code == 200
    assert response.json()["namespace"] == "https://example.org/new-vocab"
    assert response.json()["name"] == "No Namespace"  # Name unchanged


@pytest.mark.asyncio
async def test_update_project_change_namespace(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test changing a project's namespace."""
    # Create project with namespace
    project = Project(name="With Namespace", namespace="https://old.example.org/vocab")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    # Change namespace via update
    response = await authenticated_client.put(
        f"/api/projects/{project.id}",
        json={"namespace": "https://new.example.org/vocab"},
    )
    assert response.status_code == 200
    assert response.json()["namespace"] == "https://new.example.org/vocab"


@pytest.mark.asyncio
async def test_update_project_invalid_namespace(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test that updating to an invalid namespace fails."""
    # Create project
    project = Project(name="Test Project", namespace="https://example.org/vocab")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    # Try to update with invalid namespace
    response = await authenticated_client.put(
        f"/api/projects/{project.id}",
        json={"namespace": "not-a-valid-uri"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_project_clear_namespace(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test removing a namespace from a project."""
    # Create project with namespace
    project = Project(name="Has Namespace", namespace="https://example.org/vocab")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)

    # Clear namespace by setting to null
    response = await authenticated_client.put(
        f"/api/projects/{project.id}",
        json={"namespace": None},
    )
    assert response.status_code == 200
    assert response.json()["namespace"] is None


# Version export tests

@pytest.mark.asyncio
async def test_export_version_ttl(
    authenticated_client: AsyncClient, published_version: PublishedVersion
) -> None:
    """Test exporting a published version as Turtle."""
    project_id = published_version.project_id
    response = await authenticated_client.get(
        f"/api/projects/{project_id}/versions/1.0/export"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/turtle; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert ".ttl" in response.headers["content-disposition"]

    content = response.text
    assert "@prefix" in content
    assert "skos:ConceptScheme" in content


@pytest.mark.asyncio
async def test_export_version_contains_concepts(
    authenticated_client: AsyncClient, published_version: PublishedVersion
) -> None:
    """Test that the exported version contains expected concepts."""
    project_id = published_version.project_id
    response = await authenticated_client.get(
        f"/api/projects/{project_id}/versions/1.0/export"
    )

    content = response.text
    assert "Animals" in content
    assert "Mammals" in content
    assert "skos:broader" in content


@pytest.mark.asyncio
async def test_export_version_filename(
    authenticated_client: AsyncClient, published_version: PublishedVersion
) -> None:
    """Test that the filename is based on the version title."""
    project_id = published_version.project_id
    response = await authenticated_client.get(
        f"/api/projects/{project_id}/versions/1.0/export"
    )

    disposition = response.headers["content-disposition"]
    assert "v1-0.ttl" in disposition


@pytest.mark.asyncio
async def test_export_version_xml(
    authenticated_client: AsyncClient, published_version: PublishedVersion
) -> None:
    """Test exporting a published version as RDF/XML."""
    project_id = published_version.project_id
    response = await authenticated_client.get(
        f"/api/projects/{project_id}/versions/1.0/export?format=xml"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/rdf+xml; charset=utf-8"
    assert ".rdf" in response.headers["content-disposition"]

    content = response.text
    assert "<?xml" in content or "<rdf:RDF" in content


@pytest.mark.asyncio
async def test_export_version_jsonld(
    authenticated_client: AsyncClient, published_version: PublishedVersion
) -> None:
    """Test exporting a published version as JSON-LD."""
    import json

    project_id = published_version.project_id
    response = await authenticated_client.get(
        f"/api/projects/{project_id}/versions/1.0/export?format=jsonld"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/ld+json; charset=utf-8"
    assert ".jsonld" in response.headers["content-disposition"]

    data = json.loads(response.text)
    assert isinstance(data, (dict, list))


@pytest.mark.asyncio
async def test_export_version_not_found(
    authenticated_client: AsyncClient, published_version: PublishedVersion
) -> None:
    """Test that exporting a non-existent version returns 404."""
    project_id = published_version.project_id
    response = await authenticated_client.get(
        f"/api/projects/{project_id}/versions/99.0/export"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_version_project_not_found(
    authenticated_client: AsyncClient,
) -> None:
    """Test that exporting from a non-existent project returns 404."""
    fake_id = uuid4()
    response = await authenticated_client.get(
        f"/api/projects/{fake_id}/versions/1.0/export"
    )

    assert response.status_code == 404
