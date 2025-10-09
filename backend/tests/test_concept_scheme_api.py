"""Integration tests for ConceptScheme API endpoints."""

from fastapi.testclient import TestClient

from taxonomy_builder.main import app

client = TestClient(app)


def test_post_scheme_returns_201():
    """Test that POST /api/taxonomies/{taxonomy_id}/schemes returns 201 Created."""
    # First create a taxonomy
    taxonomy_response = client.post(
        "/api/taxonomies",
        json={
            "id": "scheme-test-taxonomy",
            "name": "Scheme Test Taxonomy",
            "uri_prefix": "http://example.org/scheme-test/",
        },
    )
    assert taxonomy_response.status_code == 201

    # Now create a scheme
    response = client.post(
        "/api/taxonomies/scheme-test-taxonomy/schemes",
        json={
            "id": "intervention",
            "name": "Intervention",
            "description": "Intervention scheme",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "intervention"
    assert data["taxonomy_id"] == "scheme-test-taxonomy"
    assert data["name"] == "Intervention"
    assert data["description"] == "Intervention scheme"
    assert data["uri"] == "http://example.org/scheme-test/intervention"
    assert "created_at" in data


def test_post_scheme_returns_404_for_invalid_taxonomy():
    """Test that POST returns 404 if taxonomy doesn't exist."""
    response = client.post(
        "/api/taxonomies/nonexistent-taxonomy/schemes",
        json={
            "id": "test",
            "name": "Test Scheme",
        },
    )

    assert response.status_code == 404
    assert "not found" in response.text.lower()


def test_post_scheme_returns_409_for_duplicate():
    """Test that POST returns 409 Conflict for duplicate scheme ID within taxonomy."""
    # Create a taxonomy
    client.post(
        "/api/taxonomies",
        json={
            "id": "duplicate-scheme-taxonomy",
            "name": "Duplicate Scheme Taxonomy",
            "uri_prefix": "http://example.org/duplicate-scheme/",
        },
    )

    # Create first scheme
    response1 = client.post(
        "/api/taxonomies/duplicate-scheme-taxonomy/schemes",
        json={
            "id": "duplicate-scheme",
            "name": "First",
        },
    )
    assert response1.status_code == 201

    # Try to create with same ID
    response2 = client.post(
        "/api/taxonomies/duplicate-scheme-taxonomy/schemes",
        json={
            "id": "duplicate-scheme",
            "name": "Second",
        },
    )

    assert response2.status_code == 409
    assert "already exists" in response2.text.lower()


# Step 10 Part A: List ConceptSchemes


def test_get_schemes_returns_200():
    """Test that GET /api/taxonomies/{taxonomy_id}/schemes returns 200 with list."""
    # Create a taxonomy
    client.post(
        "/api/taxonomies",
        json={
            "id": "list-scheme-taxonomy",
            "name": "List Scheme Taxonomy",
            "uri_prefix": "http://example.org/list-scheme/",
        },
    )

    # Create some schemes
    client.post(
        "/api/taxonomies/list-scheme-taxonomy/schemes",
        json={"id": "scheme1", "name": "Scheme 1"},
    )
    client.post(
        "/api/taxonomies/list-scheme-taxonomy/schemes",
        json={"id": "scheme2", "name": "Scheme 2"},
    )

    # List schemes
    response = client.get("/api/taxonomies/list-scheme-taxonomy/schemes")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    ids = [s["id"] for s in data]
    assert "scheme1" in ids
    assert "scheme2" in ids


def test_get_schemes_filters_by_taxonomy():
    """Test that GET returns only schemes for the specified taxonomy."""
    # Create two taxonomies
    client.post(
        "/api/taxonomies",
        json={
            "id": "filter-taxonomy-1",
            "name": "Filter Taxonomy 1",
            "uri_prefix": "http://example.org/filter1/",
        },
    )
    client.post(
        "/api/taxonomies",
        json={
            "id": "filter-taxonomy-2",
            "name": "Filter Taxonomy 2",
            "uri_prefix": "http://example.org/filter2/",
        },
    )

    # Create schemes in different taxonomies
    client.post(
        "/api/taxonomies/filter-taxonomy-1/schemes",
        json={"id": "scheme-a", "name": "Scheme A"},
    )
    client.post(
        "/api/taxonomies/filter-taxonomy-2/schemes",
        json={"id": "scheme-b", "name": "Scheme B"},
    )

    # List schemes for taxonomy 1
    response = client.get("/api/taxonomies/filter-taxonomy-1/schemes")

    assert response.status_code == 200
    data = response.json()
    ids = [s["id"] for s in data]
    assert "scheme-a" in ids
    assert "scheme-b" not in ids


def test_get_schemes_returns_404_for_invalid_taxonomy():
    """Test that GET returns 404 if taxonomy doesn't exist."""
    response = client.get("/api/taxonomies/nonexistent-taxonomy/schemes")

    assert response.status_code == 404
    assert "not found" in response.text.lower()


# Step 10 Part B: Get ConceptScheme by ID


def test_get_scheme_returns_200():
    """Test that GET /api/schemes/{scheme_id} returns 200 with scheme."""
    # Create a taxonomy
    client.post(
        "/api/taxonomies",
        json={
            "id": "get-scheme-taxonomy",
            "name": "Get Scheme Taxonomy",
            "uri_prefix": "http://example.org/get-scheme/",
        },
    )

    # Create a scheme
    create_response = client.post(
        "/api/taxonomies/get-scheme-taxonomy/schemes",
        json={"id": "get-scheme-test", "name": "Get Scheme Test"},
    )
    assert create_response.status_code == 201

    # Get it by ID
    response = client.get("/api/schemes/get-scheme-test")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "get-scheme-test"
    assert data["taxonomy_id"] == "get-scheme-taxonomy"
    assert data["name"] == "Get Scheme Test"


def test_get_scheme_returns_404_when_not_found():
    """Test that GET /api/schemes/{scheme_id} returns 404 for nonexistent ID."""
    response = client.get("/api/schemes/nonexistent-scheme")

    assert response.status_code == 404
    assert "not found" in response.text.lower()


# Step 11 Part A: Update ConceptScheme


def test_put_scheme_returns_200():
    """Test that PUT /api/schemes/{scheme_id} returns 200 with updated scheme."""
    # Create a taxonomy
    client.post(
        "/api/taxonomies",
        json={
            "id": "update-scheme-taxonomy",
            "name": "Update Scheme Taxonomy",
            "uri_prefix": "http://example.org/update-scheme/",
        },
    )

    # Create a scheme
    create_response = client.post(
        "/api/taxonomies/update-scheme-taxonomy/schemes",
        json={"id": "update-test", "name": "Original Name"},
    )
    assert create_response.status_code == 201

    # Update it
    update_response = client.put(
        "/api/schemes/update-test",
        json={"name": "Updated Name", "description": "Updated description"},
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == "update-test"
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


def test_put_scheme_returns_404_when_not_found():
    """Test that PUT /api/schemes/{scheme_id} returns 404 for nonexistent ID."""
    response = client.put("/api/schemes/nonexistent-scheme", json={"name": "New Name"})

    assert response.status_code == 404
    assert "not found" in response.text.lower()


# Step 11 Part B: Delete ConceptScheme


def test_delete_scheme_returns_204():
    """Test that DELETE /api/schemes/{scheme_id} returns 204 No Content."""
    # Create a taxonomy
    client.post(
        "/api/taxonomies",
        json={
            "id": "delete-scheme-taxonomy",
            "name": "Delete Scheme Taxonomy",
            "uri_prefix": "http://example.org/delete-scheme/",
        },
    )

    # Create a scheme
    create_response = client.post(
        "/api/taxonomies/delete-scheme-taxonomy/schemes",
        json={"id": "delete-test", "name": "To Be Deleted"},
    )
    assert create_response.status_code == 201

    # Delete it
    delete_response = client.delete("/api/schemes/delete-test")

    assert delete_response.status_code == 204


def test_delete_scheme_returns_404_when_not_found():
    """Test that DELETE /api/schemes/{scheme_id} returns 404 for nonexistent ID."""
    response = client.delete("/api/schemes/nonexistent-scheme")

    assert response.status_code == 404
    assert "not found" in response.text.lower()
