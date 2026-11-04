"""Shared validation utilities for Pydantic schemas."""

import re

# Pattern for URI-safe identifiers: alphanumeric, underscores, hyphens, starting with letter
IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")


def validate_identifier(v: str | None) -> str | None:
    """Validate that a value is a URI-safe identifier.

    Returns None unchanged. Strips whitespace from non-None values.

    Raises:
        ValueError: If the identifier is empty, doesn't start with a letter,
            or contains non-URI-safe characters.
    """
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("identifier must not be empty")
    if not v[0].isalpha():
        raise ValueError("identifier must start with a letter")
    if not IDENTIFIER_PATTERN.match(v):
        raise ValueError(
            "identifier must be URI-safe: alphanumeric, underscores, and hyphens only"
        )
    return v


def uri_local_name(uri: str) -> str:
    """The part of a URI after its last ``#``, or after its last ``/`` if it has no ``#``."""
    for sep in ("#", "/"):
        idx = uri.rfind(sep)
        if idx >= 0:
            return uri[idx + 1 :]
    return uri


def check_uri_matches_identifier(identifier: str, uri: str | None) -> None:
    """Keep an explicit URI's local name and the identifier interchangeable.

    Raises:
        ValueError: If the URI's local name differs from the identifier.
    """
    if uri is not None and uri_local_name(uri) != identifier:
        raise ValueError(
            f"identifier '{identifier}' must match the URI's local name "
            f"'{uri_local_name(uri)}'"
        )
