"""Tests for the versions API."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.concept import ConceptCreate
from taxonomy_builder.services.concept_service import ConceptService


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project")
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
        uri="http://example.org/concepts",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.mark.asyncio
async def test_publish_version(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test creating/publishing a version."""
    response = await client.post(
        f"/api/schemes/{scheme.id}/versions",
        json={"version_label": "1.0", "notes": "Initial release"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["version_label"] == "1.0"
    assert data["notes"] == "Initial release"
    assert data["scheme_id"] == str(scheme.id)
    assert "snapshot" in data
    assert "id" in data


@pytest.mark.asyncio
async def test_list_versions(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test listing versions for a scheme."""
    # Create versions
    await client.post(
        f"/api/schemes/{scheme.id}/versions",
        json={"version_label": "1.0"},
    )
    await client.post(
        f"/api/schemes/{scheme.id}/versions",
        json={"version_label": "2.0"},
    )

    response = await client.get(f"/api/schemes/{scheme.id}/versions")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Should be ordered by published_at descending
    assert data[0]["version_label"] == "2.0"
    assert data[1]["version_label"] == "1.0"


@pytest.mark.asyncio
async def test_get_version(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test getting a specific version."""
    # Create a version
    create_response = await client.post(
        f"/api/schemes/{scheme.id}/versions",
        json={"version_label": "1.0"},
    )
    version_id = create_response.json()["id"]

    response = await client.get(f"/api/versions/{version_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == version_id
    assert data["version_label"] == "1.0"


@pytest.mark.asyncio
async def test_get_version_not_found(client: AsyncClient) -> None:
    """Test 404 for non-existent version."""
    response = await client.get(f"/api/versions/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_version_ttl(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test exporting a version as Turtle (default format)."""
    # Create a version
    create_response = await client.post(
        f"/api/schemes/{scheme.id}/versions",
        json={"version_label": "1.0"},
    )
    version_id = create_response.json()["id"]

    response = await client.get(f"/api/versions/{version_id}/export")

    assert response.status_code == 200
    assert "text/turtle" in response.headers["content-type"]
    # Should have Content-Disposition header with filename
    assert "Content-Disposition" in response.headers
    assert "test-scheme-v1.0.ttl" in response.headers["Content-Disposition"]
    # Should contain SKOS content
    content = response.text
    assert "skos:ConceptScheme" in content or "ConceptScheme" in content


@pytest.mark.asyncio
async def test_export_version_jsonld(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test exporting a version as JSON-LD."""
    # Create a version
    create_response = await client.post(
        f"/api/schemes/{scheme.id}/versions",
        json={"version_label": "1.0"},
    )
    version_id = create_response.json()["id"]

    response = await client.get(f"/api/versions/{version_id}/export?format=jsonld")

    assert response.status_code == 200
    assert "application/ld+json" in response.headers["content-type"]
    assert "test-scheme-v1.0.jsonld" in response.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_export_version_xml(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test exporting a version as RDF/XML."""
    # Create a version
    create_response = await client.post(
        f"/api/schemes/{scheme.id}/versions",
        json={"version_label": "1.0"},
    )
    version_id = create_response.json()["id"]

    response = await client.get(f"/api/versions/{version_id}/export?format=xml")

    assert response.status_code == 200
    assert "application/rdf+xml" in response.headers["content-type"]
    assert "test-scheme-v1.0.rdf" in response.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_duplicate_version_label_returns_409(
    client: AsyncClient, db_session: AsyncSession, scheme: ConceptScheme
) -> None:
    """Test that publishing with duplicate label returns 409."""
    await client.post(
        f"/api/schemes/{scheme.id}/versions",
        json={"version_label": "1.0"},
    )

    response = await client.post(
        f"/api/schemes/{scheme.id}/versions",
        json={"version_label": "1.0"},
    )

    assert response.status_code == 409
