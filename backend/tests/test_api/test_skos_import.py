"""Tests for SKOS Import API endpoint."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a project for testing."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


# Sample SKOS files for testing

SIMPLE_SCHEME_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:TestScheme a skos:ConceptScheme ;
    rdfs:label "Test Scheme" ;
    rdfs:comment "A test concept scheme" .

ex:Concept1 a skos:Concept ;
    skos:inScheme ex:TestScheme ;
    skos:prefLabel "First Concept" ;
    skos:definition "The first concept" .

ex:Concept2 a skos:Concept ;
    skos:inScheme ex:TestScheme ;
    skos:prefLabel "Second Concept" ;
    skos:broader ex:Concept1 .
"""

MULTI_SCHEME_TTL = b"""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:SchemeA a skos:ConceptScheme ;
    rdfs:label "Scheme A" .

ex:SchemeB a skos:ConceptScheme ;
    rdfs:label "Scheme B" .

ex:ConceptA1 a skos:Concept ;
    skos:inScheme ex:SchemeA ;
    skos:prefLabel "Concept A1" .

ex:ConceptB1 a skos:Concept ;
    skos:inScheme ex:SchemeB ;
    skos:prefLabel "Concept B1" .
"""

INVALID_RDF = b"This is not valid RDF content."


# Preview tests (dry_run=true)


@pytest.mark.asyncio
async def test_import_preview_simple_scheme(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Test previewing a simple single-scheme file."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.ttl", SIMPLE_SCHEME_TTL, "text/turtle")},
        params={"dry_run": "true"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert len(data["schemes"]) == 1
    assert data["schemes"][0]["title"] == "Test Scheme"
    assert data["schemes"][0]["concepts_count"] == 2
    assert data["schemes"][0]["relationships_count"] == 1
    assert data["total_concepts_count"] == 2
    assert data["total_relationships_count"] == 1


@pytest.mark.asyncio
async def test_import_preview_multiple_schemes(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Test previewing a file with multiple schemes."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.ttl", MULTI_SCHEME_TTL, "text/turtle")},
        params={"dry_run": "true"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert len(data["schemes"]) == 2
    assert data["total_concepts_count"] == 2


@pytest.mark.asyncio
async def test_import_preview_default_dry_run(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Test that dry_run defaults to true."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.ttl", SIMPLE_SCHEME_TTL, "text/turtle")},
        # No dry_run param - should default to true
    )

    assert response.status_code == 200
    data = response.json()

    # Should be a preview response (has "valid" and "schemes")
    assert "valid" in data
    assert "schemes" in data


# Execute tests (dry_run=false)


@pytest.mark.asyncio
async def test_import_execute_simple_scheme(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Test executing import of a simple scheme."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.ttl", SIMPLE_SCHEME_TTL, "text/turtle")},
        params={"dry_run": "false"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "schemes_created" in data
    assert len(data["schemes_created"]) == 1
    assert data["schemes_created"][0]["title"] == "Test Scheme"
    assert data["schemes_created"][0]["concepts_created"] == 2
    assert data["total_concepts_created"] == 2
    assert data["total_relationships_created"] == 1

    # Verify scheme was created by fetching it
    scheme_id = data["schemes_created"][0]["id"]
    get_response = await authenticated_client.get(f"/api/schemes/{scheme_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Test Scheme"


@pytest.mark.asyncio
async def test_import_execute_multiple_schemes(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Test executing import of multiple schemes."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.ttl", MULTI_SCHEME_TTL, "text/turtle")},
        params={"dry_run": "false"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["schemes_created"]) == 2
    assert data["total_concepts_created"] == 2


# Error tests


@pytest.mark.asyncio
async def test_import_project_not_found(authenticated_client: AsyncClient) -> None:
    """Test import returns 404 for non-existent project."""
    response = await authenticated_client.post(
        f"/api/projects/{uuid4()}/import",
        files={"file": ("test.ttl", SIMPLE_SCHEME_TTL, "text/turtle")},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_import_invalid_rdf(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Test import returns 400 for invalid RDF."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.ttl", INVALID_RDF, "text/turtle")},
    )

    assert response.status_code == 400
    assert "parse" in response.json()["detail"].lower() or "rdf" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_unsupported_format(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Test import returns 400 for unsupported file format."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.xyz", SIMPLE_SCHEME_TTL, "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "format" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_uri_conflict(
    db_session: AsyncSession, authenticated_client: AsyncClient, project: Project
) -> None:
    """Test import returns 409 when scheme URI already exists."""
    # Create existing scheme with same URI
    existing = ConceptScheme(
        project_id=project.id,
        title="Existing Scheme",
        uri="http://example.org/TestScheme",
    )
    db_session.add(existing)
    await db_session.flush()

    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.ttl", SIMPLE_SCHEME_TTL, "text/turtle")},
    )

    assert response.status_code == 409
    assert "uri" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_title_conflict_auto_rename(
    db_session: AsyncSession, authenticated_client: AsyncClient, project: Project
) -> None:
    """Test that title conflict results in auto-rename on execute."""
    # Create existing scheme with same title but different URI
    existing = ConceptScheme(
        project_id=project.id,
        title="Test Scheme",
        uri="http://example.org/different-uri",
    )
    db_session.add(existing)
    await db_session.flush()

    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.ttl", SIMPLE_SCHEME_TTL, "text/turtle")},
        params={"dry_run": "false"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should succeed with renamed title
    assert data["schemes_created"][0]["title"] == "Test Scheme (2)"


# Format detection tests


@pytest.mark.asyncio
async def test_import_rdf_xml_format(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Test import with RDF/XML format."""
    rdf_xml = b"""<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:skos="http://www.w3.org/2004/02/skos/core#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
  <skos:ConceptScheme rdf:about="http://example.org/XMLScheme">
    <rdfs:label>XML Test Scheme</rdfs:label>
  </skos:ConceptScheme>
</rdf:RDF>
"""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
        files={"file": ("test.rdf", rdf_xml, "application/rdf+xml")},
        params={"dry_run": "true"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["schemes"][0]["title"] == "XML Test Scheme"


@pytest.mark.asyncio
async def test_import_no_file(
    authenticated_client: AsyncClient, project: Project
) -> None:
    """Test import returns 422 when no file provided."""
    response = await authenticated_client.post(
        f"/api/projects/{project.id}/import",
    )

    assert response.status_code == 422
