"""Tests for the Ontology API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_ontology_returns_classes_and_properties(
    authenticated_client: AsyncClient,
) -> None:
    """Test that GET /api/ontology returns classes and properties."""
    response = await authenticated_client.get("/api/ontology")
    assert response.status_code == 200

    data = response.json()
    assert "classes" in data
    assert "object_properties" in data
    assert "datatype_properties" in data

    # Should have parsed classes from the bundled ontology
    assert len(data["classes"]) > 0
    assert len(data["object_properties"]) > 0
    assert len(data["datatype_properties"]) > 0


@pytest.mark.asyncio
async def test_classes_have_uri_label_comment(
    authenticated_client: AsyncClient,
) -> None:
    """Test that classes have uri, label, and comment fields."""
    response = await authenticated_client.get("/api/ontology")
    assert response.status_code == 200

    data = response.json()
    classes = data["classes"]

    # Find the Investigation class from the core ontology
    investigation = next(
        (c for c in classes if "Investigation" in c["uri"]), None
    )
    assert investigation is not None
    assert "uri" in investigation
    assert "label" in investigation
    assert "comment" in investigation
    assert investigation["label"] == "Investigation"


@pytest.mark.asyncio
async def test_object_properties_have_domain_and_range(
    authenticated_client: AsyncClient,
) -> None:
    """Test that object properties have domain and range as lists."""
    response = await authenticated_client.get("/api/ontology")
    assert response.status_code == 200

    data = response.json()
    object_properties = data["object_properties"]

    # Find the hasFinding property
    has_finding = next(
        (p for p in object_properties if "hasFinding" in p["uri"]), None
    )
    assert has_finding is not None
    assert "uri" in has_finding
    assert "label" in has_finding
    assert "domain" in has_finding
    assert "range" in has_finding
    assert "property_type" in has_finding

    # Domain and range should be lists
    assert isinstance(has_finding["domain"], list)
    assert isinstance(has_finding["range"], list)
    assert has_finding["property_type"] == "object"


@pytest.mark.asyncio
async def test_datatype_properties_have_range_datatype(
    authenticated_client: AsyncClient,
) -> None:
    """Test that datatype properties have XSD datatypes in range."""
    response = await authenticated_client.get("/api/ontology")
    assert response.status_code == 200

    data = response.json()
    datatype_properties = data["datatype_properties"]

    # Find the sampleSize property
    sample_size = next(
        (p for p in datatype_properties if "sampleSize" in p["uri"]), None
    )
    assert sample_size is not None
    assert "range" in sample_size
    assert sample_size["property_type"] == "datatype"

    # Range should contain XSD datatype
    assert any("XMLSchema" in r for r in sample_size["range"])
