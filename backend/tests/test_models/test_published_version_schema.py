"""Tests for the PublishRequest Pydantic schema."""

import pytest
from pydantic import ValidationError

from taxonomy_builder.schemas.published_version import PublishRequest


class TestPublishRequest:
    """Tests for PublishRequest schema."""

    def test_valid_major_minor(self) -> None:
        """Test valid major.minor version."""
        req = PublishRequest(version="1.0", title="Release")
        assert req.version == "1.0"

    def test_valid_major_minor_patch(self) -> None:
        """Test valid major.minor.patch version."""
        req = PublishRequest(version="1.0.1", title="Patch Release")
        assert req.version == "1.0.1"

    def test_valid_zero_version(self) -> None:
        """Test valid zero-prefixed version."""
        req = PublishRequest(version="0.1", title="Pre-release")
        assert req.version == "0.1"

    def test_valid_large_numbers(self) -> None:
        """Test valid version with large numbers."""
        req = PublishRequest(version="10.20", title="Big Release")
        assert req.version == "10.20"

    def test_invalid_v_prefix(self) -> None:
        """Test that v prefix is rejected."""
        with pytest.raises(ValidationError, match="version"):
            PublishRequest(version="v1.0", title="Release")

    def test_invalid_single_number(self) -> None:
        """Test that a single number is rejected."""
        with pytest.raises(ValidationError, match="version"):
            PublishRequest(version="1", title="Release")

    def test_invalid_prerelease_suffix(self) -> None:
        """Test that pre-release suffixes are rejected."""
        with pytest.raises(ValidationError, match="version"):
            PublishRequest(version="1.0.0-beta", title="Release")

    def test_invalid_alpha(self) -> None:
        """Test that alphabetic strings are rejected."""
        with pytest.raises(ValidationError, match="version"):
            PublishRequest(version="abc", title="Release")

    def test_invalid_empty_string(self) -> None:
        """Test that empty string is rejected."""
        with pytest.raises(ValidationError, match="version"):
            PublishRequest(version="", title="Release")

    def test_invalid_four_parts(self) -> None:
        """Test that four-part versions are rejected."""
        with pytest.raises(ValidationError, match="version"):
            PublishRequest(version="1.0.0.0", title="Release")

    def test_title_required(self) -> None:
        """Test that title is required."""
        with pytest.raises(ValidationError, match="title"):
            PublishRequest(version="1.0")  # type: ignore[call-arg]

    def test_title_stripped(self) -> None:
        """Test that title whitespace is stripped."""
        req = PublishRequest(version="1.0", title="  Spaced Title  ")
        assert req.title == "Spaced Title"

    def test_title_cannot_be_empty(self) -> None:
        """Test that empty/whitespace-only title is rejected."""
        with pytest.raises(ValidationError, match="title"):
            PublishRequest(version="1.0", title="   ")

    def test_notes_optional(self) -> None:
        """Test that notes is optional."""
        req = PublishRequest(version="1.0", title="Release")
        assert req.notes is None

    def test_notes_provided(self) -> None:
        """Test that notes can be provided."""
        req = PublishRequest(version="1.0", title="Release", notes="Some notes")
        assert req.notes == "Some notes"

    def test_publisher_optional(self) -> None:
        """Test that publisher is optional."""
        req = PublishRequest(version="1.0", title="Release")
        assert req.publisher is None

    def test_publisher_provided(self) -> None:
        """Test that publisher can be provided."""
        req = PublishRequest(version="1.0", title="Release", publisher="ESI")
        assert req.publisher == "ESI"

    def test_version_stripped(self) -> None:
        """Test that version whitespace is stripped."""
        req = PublishRequest(version="  1.0  ", title="Release")
        assert req.version == "1.0"
