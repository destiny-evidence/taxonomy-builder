"""Tests for the MCP CLI entry point."""

from taxonomy_builder.mcp.cli import main


def test_main_is_callable():
    """The CLI entry point should be a callable function."""
    assert callable(main)
