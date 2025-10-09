"""Integration tests for Taxonomy API endpoints."""

from fastapi.testclient import TestClient

from taxonomy_builder.main import app

client = TestClient(app)


def test_post_taxonomy_returns_201_created():
    """Test that POST /api/taxonomies returns 201 Created."""
    response = client.post(
        "/api/taxonomies",
        json={
            "id": "climate-health",
            "name": "Climate & Health",
            "uri_prefix": "http://example.org/climate/",
        },
    )

    assert response.status_code == 201


def test_post_taxonomy_returns_created_taxonomy():
    """Test that POST returns the created taxonomy with correct structure."""
    response = client.post(
        "/api/taxonomies",
        json={
            "id": "test-taxonomy",
            "name": "Test Taxonomy",
            "uri_prefix": "http://example.org/test/",
            "description": "A test taxonomy",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test-taxonomy"
    assert data["name"] == "Test Taxonomy"
    assert data["uri_prefix"] == "http://example.org/test/"
    assert data["description"] == "A test taxonomy"
    assert "created_at" in data


def test_post_taxonomy_validates_required_fields():
    """Test that missing required fields return 422 Unprocessable Entity."""
    # Missing id
    response = client.post(
        "/api/taxonomies",
        json={"name": "Test", "uri_prefix": "http://example.org/test/"},
    )
    assert response.status_code == 422

    # Missing name
    response = client.post(
        "/api/taxonomies",
        json={"id": "test", "uri_prefix": "http://example.org/test/"},
    )
    assert response.status_code == 422

    # Missing uri_prefix
    response = client.post(
        "/api/taxonomies",
        json={"id": "test", "name": "Test"},
    )
    assert response.status_code == 422


def test_post_taxonomy_validates_uri_prefix_format():
    """Test that invalid URI prefix returns 422."""
    response = client.post(
        "/api/taxonomies",
        json={
            "id": "test",
            "name": "Test",
            "uri_prefix": "not-a-valid-uri",
        },
    )

    assert response.status_code == 422
    assert "uri" in response.text.lower() or "invalid" in response.text.lower()


def test_post_taxonomy_rejects_duplicate_id():
    """Test that duplicate IDs return 409 Conflict."""
    # Create first taxonomy
    response1 = client.post(
        "/api/taxonomies",
        json={
            "id": "duplicate-test",
            "name": "First",
            "uri_prefix": "http://example.org/first/",
        },
    )
    assert response1.status_code == 201

    # Try to create with same ID
    response2 = client.post(
        "/api/taxonomies",
        json={
            "id": "duplicate-test",
            "name": "Second",
            "uri_prefix": "http://example.org/second/",
        },
    )
    assert response2.status_code == 409
    assert "already exists" in response2.text.lower()


def test_post_taxonomy_validates_id_format():
    """Test that invalid ID format returns 422."""
    invalid_ids = ["Invalid-ID", "invalid_id", "invalid id", ""]

    for invalid_id in invalid_ids:
        response = client.post(
            "/api/taxonomies",
            json={
                "id": invalid_id,
                "name": "Test",
                "uri_prefix": "http://example.org/test/",
            },
        )
        assert response.status_code == 422, f"ID '{invalid_id}' should be rejected"


def test_post_taxonomy_accepts_valid_id_formats():
    """Test that valid ID formats are accepted."""
    valid_ids = ["valid-slug", "valid-slug-123", "validslug", "valid123"]

    for valid_id in valid_ids:
        response = client.post(
            "/api/taxonomies",
            json={
                "id": valid_id,
                "name": "Test",
                "uri_prefix": "http://example.org/test/",
            },
        )
        assert response.status_code == 201, f"ID '{valid_id}' should be accepted"


def test_post_taxonomy_description_is_optional():
    """Test that description field is optional."""
    response = client.post(
        "/api/taxonomies",
        json={
            "id": "no-description",
            "name": "No Description",
            "uri_prefix": "http://example.org/nodesc/",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["description"] is None or "description" not in data


def test_get_taxonomies_returns_200_and_empty_list():
    """Test that GET /api/taxonomies returns 200 with empty list initially."""
    # Note: This assumes fresh state or tests run in isolation
    response = client.get("/api/taxonomies")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_taxonomies_returns_created_taxonomies():
    """Test that GET /api/taxonomies returns all created taxonomies."""
    # Create some taxonomies
    client.post(
        "/api/taxonomies",
        json={
            "id": "list-test-1",
            "name": "List Test 1",
            "uri_prefix": "http://example.org/list1/",
        },
    )
    client.post(
        "/api/taxonomies",
        json={
            "id": "list-test-2",
            "name": "List Test 2",
            "uri_prefix": "http://example.org/list2/",
        },
    )

    response = client.get("/api/taxonomies")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    # Check that our created taxonomies are in the list
    ids = [t["id"] for t in data]
    assert "list-test-1" in ids
    assert "list-test-2" in ids
