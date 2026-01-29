"""Tests for SKOS Export API endpoint."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
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


@pytest.fixture
async def scheme(db_session: AsyncSession, project: Project) -> ConceptScheme:
    """Create a concept scheme for testing."""
    scheme = ConceptScheme(
        project_id=project.id,
        title="Test Taxonomy",
        description="A test taxonomy",
        uri="http://example.org/taxonomy",
        publisher="Test Publisher",
        version="1.0",
    )
    db_session.add(scheme)
    await db_session.flush()
    await db_session.refresh(scheme)
    return scheme


@pytest.fixture
async def scheme_with_concepts(
    db_session: AsyncSession, scheme: ConceptScheme
) -> ConceptScheme:
    """Create a scheme with concepts for testing."""
    animals = Concept(
        scheme_id=scheme.id,
        pref_label="Animals",
        identifier="animals",
        definition="Living organisms",
    )
    mammals = Concept(
        scheme_id=scheme.id,
        pref_label="Mammals",
        identifier="mammals",
    )
    db_session.add_all([animals, mammals])
    await db_session.flush()

    # Add hierarchy
    rel = ConceptBroader(concept_id=mammals.id, broader_concept_id=animals.id)
    db_session.add(rel)
    await db_session.flush()

    return scheme


# Format tests


@pytest.mark.asyncio
async def test_export_turtle_default(
    authenticated_client: AsyncClient, scheme_with_concepts: ConceptScheme
) -> None:
    """Test export in Turtle format (default)."""
    response = await authenticated_client.get(f"/api/schemes/{scheme_with_concepts.id}/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/turtle; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert ".ttl" in response.headers["content-disposition"]

    # Should be valid Turtle content
    content = response.text
    assert "@prefix" in content
    assert "skos:ConceptScheme" in content


@pytest.mark.asyncio
async def test_export_turtle_explicit(
    authenticated_client: AsyncClient, scheme_with_concepts: ConceptScheme
) -> None:
    """Test export with explicit Turtle format."""
    response = await authenticated_client.get(
        f"/api/schemes/{scheme_with_concepts.id}/export?format=ttl"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/turtle; charset=utf-8"


@pytest.mark.asyncio
async def test_export_rdf_xml(
    authenticated_client: AsyncClient, scheme_with_concepts: ConceptScheme
) -> None:
    """Test export in RDF/XML format."""
    response = await authenticated_client.get(
        f"/api/schemes/{scheme_with_concepts.id}/export?format=xml"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/rdf+xml; charset=utf-8"
    assert ".rdf" in response.headers["content-disposition"]

    # Should be valid XML
    content = response.text
    assert "<?xml" in content or "<rdf:RDF" in content


@pytest.mark.asyncio
async def test_export_jsonld(
    authenticated_client: AsyncClient, scheme_with_concepts: ConceptScheme
) -> None:
    """Test export in JSON-LD format."""
    response = await authenticated_client.get(
        f"/api/schemes/{scheme_with_concepts.id}/export?format=jsonld"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/ld+json; charset=utf-8"
    assert ".jsonld" in response.headers["content-disposition"]

    # Should be valid JSON
    import json

    data = json.loads(response.text)
    assert isinstance(data, (dict, list))


# Content tests


@pytest.mark.asyncio
async def test_export_contains_scheme_metadata(
    authenticated_client: AsyncClient, scheme: ConceptScheme
) -> None:
    """Test that export contains scheme metadata."""
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/export")

    content = response.text
    assert "Test Taxonomy" in content
    assert "A test taxonomy" in content
    assert "Test Publisher" in content


@pytest.mark.asyncio
async def test_export_contains_concepts(
    authenticated_client: AsyncClient, scheme_with_concepts: ConceptScheme
) -> None:
    """Test that export contains concepts."""
    response = await authenticated_client.get(f"/api/schemes/{scheme_with_concepts.id}/export")

    content = response.text
    assert "Animals" in content
    assert "Mammals" in content
    assert "skos:broader" in content


@pytest.mark.asyncio
async def test_export_filename(
    authenticated_client: AsyncClient, scheme: ConceptScheme
) -> None:
    """Test that filename is based on scheme title."""
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/export")

    disposition = response.headers["content-disposition"]
    # Should slugify the title
    assert "test-taxonomy" in disposition.lower() or "test_taxonomy" in disposition.lower()


# Error tests


@pytest.mark.asyncio
async def test_export_scheme_not_found(authenticated_client: AsyncClient) -> None:
    """Test export returns 404 for non-existent scheme."""
    response = await authenticated_client.get(f"/api/schemes/{uuid4()}/export")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_invalid_format(
    authenticated_client: AsyncClient, scheme: ConceptScheme
) -> None:
    """Test export returns 422 for invalid format."""
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/export?format=invalid")

    assert response.status_code == 422


# Empty scheme test


@pytest.mark.asyncio
async def test_export_empty_scheme(authenticated_client: AsyncClient, scheme: ConceptScheme) -> None:
    """Test export works for scheme with no concepts."""
    response = await authenticated_client.get(f"/api/schemes/{scheme.id}/export")

    assert response.status_code == 200
    content = response.text
    assert "skos:ConceptScheme" in content
    # Should not have "a skos:Concept" (only "a skos:ConceptScheme")
    assert "a skos:Concept ;" not in content
