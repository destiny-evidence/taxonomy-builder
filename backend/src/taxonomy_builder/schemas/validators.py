"""Shared validation utilities for Pydantic schemas."""

import re
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator


class UpdateSchema(BaseModel):
    """Base for partial updates: omitted fields are unchanged, explicit null clears.

    Fields listed in ``non_nullable`` may be omitted but not set to null.
    """

    model_config = ConfigDict(extra="forbid")

    non_nullable: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def reject_null_on_non_nullable(self) -> Self:
        set_to_null = {name for name in self.model_fields_set if getattr(self, name) is None}
        if rejected := set_to_null & self.non_nullable:
            raise ValueError(f"{', '.join(rejected)} cannot be set to null")
        return self


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
