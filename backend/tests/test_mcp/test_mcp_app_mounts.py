"""Test that the MCP app is properly mounted."""

from taxonomy_builder.main import app


def test_mcp_route_exists():
    """The MCP endpoint should be mounted at /mcp."""
    routes = [r.path for r in app.routes]
    assert "/mcp" in routes or any("/mcp" in str(r.path) for r in app.routes)
