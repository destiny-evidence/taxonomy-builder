"""Pydantic schemas for vocabulary publishing."""

import re

from pydantic import BaseModel, Field, field_validator

SEMVER_PATTERN = re.compile(r"^\d+\.\d+(\.\d+)?$")


class PublishRequest(BaseModel):
    """Request body for publishing a project version."""

    version: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    notes: str | None = None

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        v = v.strip()
        if not SEMVER_PATTERN.match(v):
            raise ValueError(
                "version must be semver: MAJOR.MINOR or MAJOR.MINOR.PATCH (e.g. 1.0, 1.0.1)"
            )
        return v

    @field_validator("title")
    @classmethod
    def strip_and_validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v
