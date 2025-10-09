"""Tests for the main FastAPI application."""

from fastapi.testclient import TestClient


def test_app_can_be_imported():
    """Test that the FastAPI app can be imported."""
    from taxonomy_builder.main import app

    assert app is not None


def test_health_check_endpoint():
    """Test the health check endpoint returns 200 OK."""
    from taxonomy_builder.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_app_has_cors_middleware():
    """Test that CORS middleware is configured."""
    from fastapi.testclient import TestClient

    from taxonomy_builder.main import app

    # Test CORS headers are present in response
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    # CORS middleware should add these headers
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
