"""Integration tests for Concept API endpoints."""

import pytest
from fastapi.testclient import TestClient

from taxonomy_builder.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_repositories():
    """Reset all repositories before each test."""
    from taxonomy_builder.api.concepts import concept_repository, scheme_repository
    from taxonomy_builder.api.taxonomies import _repository as taxonomy_repository

    concept_repository._concepts.clear()
    scheme_repository._schemes.clear()
    taxonomy_repository._taxonomies.clear()


def create_taxonomy(taxonomy_id="test-taxonomy"):
    """Helper to create a taxonomy."""
    return client.post(
        "/api/taxonomies",
        json={
            "id": taxonomy_id,
            "name": "Test Taxonomy",
            "uri_prefix": "http://example.org/test/",
        },
    )


def create_scheme(taxonomy_id="test-taxonomy", scheme_id="test-scheme"):
    """Helper to create a concept scheme."""
    return client.post(
        f"/api/taxonomies/{taxonomy_id}/schemes",
        json={
            "id": scheme_id,
            "name": "Test Scheme",
        },
    )


# Step 12 Part A: Create Concept


def test_post_concept_returns_201():
    """Test POST /api/schemes/{scheme_id}/concepts returns 201."""
    create_taxonomy()
    create_scheme()

    response = client.post(
        "/api/schemes/test-scheme/concepts",
        json={
            "id": "health-outcome",
            "pref_label": "Health Outcome",
            "definition": "A health-related result",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "health-outcome"
    assert data["scheme_id"] == "test-scheme"
    assert data["pref_label"] == "Health Outcome"
    assert data["definition"] == "A health-related result"
    assert data["uri"] == "http://example.org/test/health-outcome"
    assert data["broader_ids"] == []
    assert data["narrower_ids"] == []


def test_post_concept_returns_404_for_invalid_scheme():
    """Test POST /api/schemes/{scheme_id}/concepts returns 404 for invalid scheme."""
    response = client.post(
        "/api/schemes/nonexistent/concepts",
        json={
            "id": "test",
            "pref_label": "Test",
        },
    )

    assert response.status_code == 404
    assert "ConceptScheme with ID 'nonexistent' not found" in response.json()["detail"]


def test_post_concept_returns_409_for_duplicate():
    """Test POST /api/schemes/{scheme_id}/concepts returns 409 for duplicate ID."""
    create_taxonomy()
    create_scheme()

    # Create first concept
    client.post(
        "/api/schemes/test-scheme/concepts",
        json={
            "id": "duplicate",
            "pref_label": "Duplicate",
        },
    )

    # Try to create duplicate
    response = client.post(
        "/api/schemes/test-scheme/concepts",
        json={
            "id": "duplicate",
            "pref_label": "Duplicate Again",
        },
    )

    assert response.status_code == 409
    assert "Concept with ID 'duplicate' already exists" in response.json()["detail"]


# Step 13 Part A: List Concepts


def test_get_concepts_returns_200():
    """Test GET /api/schemes/{scheme_id}/concepts returns 200."""
    create_taxonomy()
    create_scheme()

    # Create a concept
    client.post(
        "/api/schemes/test-scheme/concepts",
        json={
            "id": "concept1",
            "pref_label": "Concept 1",
        },
    )

    response = client.get("/api/schemes/test-scheme/concepts")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "concept1"


def test_get_concepts_filters_by_scheme():
    """Test GET /api/schemes/{scheme_id}/concepts only returns concepts for that scheme."""
    create_taxonomy()
    create_scheme(scheme_id="scheme1")
    create_scheme(scheme_id="scheme2")

    # Create concepts in different schemes
    client.post(
        "/api/schemes/scheme1/concepts",
        json={"id": "concept1", "pref_label": "Concept 1"},
    )
    client.post(
        "/api/schemes/scheme2/concepts",
        json={"id": "concept2", "pref_label": "Concept 2"},
    )

    response = client.get("/api/schemes/scheme1/concepts")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "concept1"


def test_get_concepts_returns_404_for_invalid_scheme():
    """Test GET /api/schemes/{scheme_id}/concepts returns 404 for invalid scheme."""
    response = client.get("/api/schemes/nonexistent/concepts")

    assert response.status_code == 404
    assert "ConceptScheme with ID 'nonexistent' not found" in response.json()["detail"]


# Step 13 Part B: Get Concept by ID


def test_get_concept_returns_200():
    """Test GET /api/concepts/{concept_id} returns 200."""
    create_taxonomy()
    create_scheme()

    client.post(
        "/api/schemes/test-scheme/concepts",
        json={
            "id": "test-concept",
            "pref_label": "Test Concept",
        },
    )

    response = client.get("/api/concepts/test-concept")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-concept"
    assert data["pref_label"] == "Test Concept"


def test_get_concept_returns_404_when_not_found():
    """Test GET /api/concepts/{concept_id} returns 404 when not found."""
    response = client.get("/api/concepts/nonexistent")

    assert response.status_code == 404
    assert "Concept with ID 'nonexistent' not found" in response.json()["detail"]


# Step 14 Part A: Update Concept


def test_put_concept_returns_200():
    """Test PUT /api/concepts/{concept_id} returns 200."""
    create_taxonomy()
    create_scheme()

    client.post(
        "/api/schemes/test-scheme/concepts",
        json={
            "id": "test-concept",
            "pref_label": "Original Label",
        },
    )

    response = client.put(
        "/api/concepts/test-concept",
        json={"pref_label": "Updated Label"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["pref_label"] == "Updated Label"


def test_put_concept_returns_404_when_not_found():
    """Test PUT /api/concepts/{concept_id} returns 404 when not found."""
    response = client.put(
        "/api/concepts/nonexistent",
        json={"pref_label": "New Label"},
    )

    assert response.status_code == 404
    assert "Concept with ID 'nonexistent' not found" in response.json()["detail"]


# Step 14 Part B: Delete Concept


def test_delete_concept_returns_204():
    """Test DELETE /api/concepts/{concept_id} returns 204."""
    create_taxonomy()
    create_scheme()

    client.post(
        "/api/schemes/test-scheme/concepts",
        json={
            "id": "test-concept",
            "pref_label": "Test Concept",
        },
    )

    response = client.delete("/api/concepts/test-concept")

    assert response.status_code == 204


def test_delete_concept_returns_404_when_not_found():
    """Test DELETE /api/concepts/{concept_id} returns 404 when not found."""
    response = client.delete("/api/concepts/nonexistent")

    assert response.status_code == 404
    assert "Concept with ID 'nonexistent' not found" in response.json()["detail"]


# Step 15 Part A: Add Broader Relationship


def test_post_broader_returns_200():
    """Test POST /api/concepts/{concept_id}/broader/{broader_id} returns 200."""
    create_taxonomy()
    create_scheme()

    client.post(
        "/api/schemes/test-scheme/concepts",
        json={"id": "parent", "pref_label": "Parent"},
    )
    client.post(
        "/api/schemes/test-scheme/concepts",
        json={"id": "child", "pref_label": "Child"},
    )

    response = client.post("/api/concepts/child/broader/parent")

    assert response.status_code == 200
    data = response.json()
    assert "parent" in data["broader_ids"]

    # Check bidirectional relationship
    parent_response = client.get("/api/concepts/parent")
    parent_data = parent_response.json()
    assert "child" in parent_data["narrower_ids"]


def test_post_broader_returns_404_for_invalid_concept():
    """Test POST /api/concepts/{concept_id}/broader/{broader_id} returns 404 for invalid concept."""
    response = client.post("/api/concepts/nonexistent/broader/parent")

    assert response.status_code == 404
    assert "Concept with ID 'nonexistent' not found" in response.json()["detail"]


def test_post_broader_returns_400_for_cycle():
    """Test POST /api/concepts/{concept_id}/broader/{broader_id} returns 400 for cycle."""
    create_taxonomy()
    create_scheme()

    client.post(
        "/api/schemes/test-scheme/concepts",
        json={"id": "concept1", "pref_label": "Concept 1"},
    )
    client.post(
        "/api/schemes/test-scheme/concepts",
        json={"id": "concept2", "pref_label": "Concept 2"},
    )

    # Create chain: concept1 -> concept2
    client.post("/api/concepts/concept1/broader/concept2")

    # Try to create cycle: concept2 -> concept1
    response = client.post("/api/concepts/concept2/broader/concept1")

    assert response.status_code == 400
    assert "cycle" in response.json()["detail"].lower()


# Step 15 Part B: Remove Broader Relationship


def test_delete_broader_returns_200():
    """Test DELETE /api/concepts/{concept_id}/broader/{broader_id} returns 200."""
    create_taxonomy()
    create_scheme()

    client.post(
        "/api/schemes/test-scheme/concepts",
        json={"id": "parent", "pref_label": "Parent"},
    )
    client.post(
        "/api/schemes/test-scheme/concepts",
        json={"id": "child", "pref_label": "Child"},
    )

    # Add relationship
    client.post("/api/concepts/child/broader/parent")

    # Remove relationship
    response = client.delete("/api/concepts/child/broader/parent")

    assert response.status_code == 200
    data = response.json()
    assert "parent" not in data["broader_ids"]

    # Check bidirectional removal
    parent_response = client.get("/api/concepts/parent")
    parent_data = parent_response.json()
    assert "child" not in parent_data["narrower_ids"]


def test_delete_broader_returns_404_for_invalid_concept():
    """Test DELETE /api/concepts/{concept_id}/broader/{broader_id} returns 404."""
    response = client.delete("/api/concepts/nonexistent/broader/parent")

    assert response.status_code == 404
    assert "Concept with ID 'nonexistent' not found" in response.json()["detail"]
