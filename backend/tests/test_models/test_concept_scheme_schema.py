"""Tests for ConceptScheme Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from taxonomy_builder.schemas.concept_scheme import (
    ConceptSchemeCreate,
    ConceptSchemeRead,
    ConceptSchemeUpdate,
)


class TestConceptSchemeCreate:
    """Tests for ConceptSchemeCreate schema."""

    def test_valid_concept_scheme_create(self) -> None:
        """Test creating a valid concept scheme."""
        scheme = ConceptSchemeCreate(
            title="Test Scheme",
            description="A test description",
            uri="http://example.org/schemes/test",
            publisher="Test Publisher",
        )
        assert scheme.title == "Test Scheme"
        assert scheme.description == "A test description"
        assert scheme.uri == "http://example.org/schemes/test"
        assert scheme.publisher == "Test Publisher"

    def test_concept_scheme_create_title_only(self) -> None:
        """Test creating a scheme with only title."""
        scheme = ConceptSchemeCreate(title="Minimal Scheme")
        assert scheme.title == "Minimal Scheme"
        assert scheme.description is None
        assert scheme.uri is None
        assert scheme.publisher is None

    def test_concept_scheme_create_requires_title(self) -> None:
        """Test that title is required."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptSchemeCreate()  # type: ignore[call-arg]
        assert "title" in str(exc_info.value)

    def test_concept_scheme_create_title_cannot_be_empty(self) -> None:
        """Test that title cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptSchemeCreate(title="")
        assert "title" in str(exc_info.value)

    def test_concept_scheme_create_title_is_stripped(self) -> None:
        """Test that title whitespace is stripped."""
        scheme = ConceptSchemeCreate(title="  Padded Title  ")
        assert scheme.title == "Padded Title"


class TestConceptSchemeUpdate:
    """Tests for ConceptSchemeUpdate schema."""

    def test_concept_scheme_update_all_fields_optional(self) -> None:
        """Test that all fields are optional for update."""
        scheme = ConceptSchemeUpdate()
        assert scheme.title is None
        assert scheme.description is None
        assert scheme.uri is None
        assert scheme.publisher is None

    def test_concept_scheme_update_with_title(self) -> None:
        """Test updating with a new title."""
        scheme = ConceptSchemeUpdate(title="New Title")
        assert scheme.title == "New Title"

    def test_concept_scheme_update_with_all_fields(self) -> None:
        """Test updating all fields."""
        scheme = ConceptSchemeUpdate(
            title="Updated Title",
            description="Updated description",
            uri="http://example.org/updated",
            publisher="Updated Publisher",
        )
        assert scheme.title == "Updated Title"
        assert scheme.description == "Updated description"
        assert scheme.uri == "http://example.org/updated"
        assert scheme.publisher == "Updated Publisher"

    def test_concept_scheme_update_title_cannot_be_empty(self) -> None:
        """Test that title cannot be empty string if provided."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptSchemeUpdate(title="")
        assert "title" in str(exc_info.value)

    def test_concept_scheme_update_title_is_stripped(self) -> None:
        """Test that title whitespace is stripped."""
        scheme = ConceptSchemeUpdate(title="  Padded  ")
        assert scheme.title == "Padded"


class TestConceptSchemeRead:
    """Tests for ConceptSchemeRead schema."""

    def test_valid_concept_scheme_read(self) -> None:
        """Test reading a valid concept scheme."""
        now = datetime.now()
        scheme_id = uuid4()
        project_id = uuid4()
        scheme = ConceptSchemeRead(
            id=scheme_id,
            project_id=project_id,
            title="Test Scheme",
            description="A description",
            uri="http://example.org/schemes/test",
            publisher="Test Publisher",
            created_at=now,
            updated_at=now,
        )
        assert scheme.id == scheme_id
        assert scheme.project_id == project_id
        assert scheme.title == "Test Scheme"
        assert scheme.description == "A description"
        assert scheme.uri == "http://example.org/schemes/test"
        assert scheme.publisher == "Test Publisher"
        assert scheme.created_at == now
        assert scheme.updated_at == now

    def test_concept_scheme_read_requires_all_fields(self) -> None:
        """Test that required fields must be provided."""
        with pytest.raises(ValidationError):
            ConceptSchemeRead()  # type: ignore[call-arg]

    def test_concept_scheme_read_optional_fields_can_be_none(self) -> None:
        """Test that optional fields can be None."""
        now = datetime.now()
        scheme = ConceptSchemeRead(
            id=uuid4(),
            project_id=uuid4(),
            title="Minimal",
            description=None,
            uri=None,
            publisher=None,
            created_at=now,
            updated_at=now,
        )
        assert scheme.description is None
        assert scheme.uri is None
        assert scheme.publisher is None
