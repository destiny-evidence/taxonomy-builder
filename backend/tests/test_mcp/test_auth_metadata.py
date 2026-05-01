"""Tests for MCP OAuth protected resource metadata (RFC 9728)."""

import pytest
from httpx import ASGITransport, AsyncClient

from taxonomy_builder.config import settings
from taxonomy_builder.main import app

requires_mcp_auth = pytest.mark.skipif(
    not settings.mcp_auth,
    reason="MCP auth disabled (TAXONOMY_MCP_AUTH=false)",
)


@requires_mcp_auth
async def test_well_known_protected_resource_metadata():
    """The server should serve OAuth protected resource metadata at the well-known URL."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/.well-known/oauth-protected-resource/mcp")

    assert resp.status_code == 200
    data = resp.json()
    assert "authorization_servers" in data
    assert len(data["authorization_servers"]) == 1
    assert "realms/destiny" in data["authorization_servers"][0]
    assert data["resource"].endswith("/mcp")


@requires_mcp_auth
async def test_well_known_cors_options():
    """The well-known endpoint should support CORS preflight."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.options("/.well-known/oauth-protected-resource/mcp")

    assert resp.status_code in (200, 204)


def test_mcp_endpoint_mounted():
    """The MCP sub-app should be mounted at /mcp."""
    mount_paths = [r.path for r in app.routes]
    assert "/mcp" in mount_paths
