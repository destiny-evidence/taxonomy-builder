"""Tests for Concept Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from taxonomy_builder.schemas.concept import (
    ConceptBrief,
    ConceptCreate,
    ConceptRead,
    ConceptUpdate,
)


class TestConceptCreate:
    """Tests for ConceptCreate schema."""

    def test_valid_concept_create(self) -> None:
        """Test creating a valid concept."""
        concept = ConceptCreate(
            pref_label="Test Concept",
            definition="A test definition",
            scope_note="Use for testing",
            uri="http://example.org/concepts/test",
        )
        assert concept.pref_label == "Test Concept"
        assert concept.definition == "A test definition"
        assert concept.scope_note == "Use for testing"
        assert concept.uri == "http://example.org/concepts/test"

    def test_concept_create_pref_label_only(self) -> None:
        """Test creating a concept with only pref_label."""
        concept = ConceptCreate(pref_label="Minimal Concept")
        assert concept.pref_label == "Minimal Concept"
        assert concept.definition is None
        assert concept.scope_note is None
        assert concept.uri is None

    def test_concept_create_requires_pref_label(self) -> None:
        """Test that pref_label is required."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptCreate()  # type: ignore[call-arg]
        assert "pref_label" in str(exc_info.value)

    def test_concept_create_pref_label_cannot_be_empty(self) -> None:
        """Test that pref_label cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptCreate(pref_label="")
        assert "pref_label" in str(exc_info.value)

    def test_concept_create_pref_label_is_stripped(self) -> None:
        """Test that pref_label whitespace is stripped."""
        concept = ConceptCreate(pref_label="  Padded Label  ")
        assert concept.pref_label == "Padded Label"


class TestConceptUpdate:
    """Tests for ConceptUpdate schema."""

    def test_concept_update_all_fields_optional(self) -> None:
        """Test that all fields are optional for update."""
        concept = ConceptUpdate()
        assert concept.pref_label is None
        assert concept.definition is None
        assert concept.scope_note is None
        assert concept.uri is None

    def test_concept_update_with_pref_label(self) -> None:
        """Test updating with a new pref_label."""
        concept = ConceptUpdate(pref_label="New Label")
        assert concept.pref_label == "New Label"

    def test_concept_update_with_all_fields(self) -> None:
        """Test updating all fields."""
        concept = ConceptUpdate(
            pref_label="Updated Label",
            definition="Updated definition",
            scope_note="Updated scope note",
            uri="http://example.org/updated",
        )
        assert concept.pref_label == "Updated Label"
        assert concept.definition == "Updated definition"
        assert concept.scope_note == "Updated scope note"
        assert concept.uri == "http://example.org/updated"

    def test_concept_update_pref_label_cannot_be_empty(self) -> None:
        """Test that pref_label cannot be empty if provided."""
        with pytest.raises(ValidationError) as exc_info:
            ConceptUpdate(pref_label="")
        assert "pref_label" in str(exc_info.value)

    def test_concept_update_pref_label_is_stripped(self) -> None:
        """Test that pref_label whitespace is stripped."""
        concept = ConceptUpdate(pref_label="  Padded  ")
        assert concept.pref_label == "Padded"


class TestConceptRead:
    """Tests for ConceptRead schema."""

    def test_valid_concept_read(self) -> None:
        """Test reading a valid concept."""
        now = datetime.now()
        concept_id = uuid4()
        scheme_id = uuid4()
        concept = ConceptRead(
            id=concept_id,
            scheme_id=scheme_id,
            pref_label="Test Concept",
            definition="A definition",
            scope_note="A scope note",
            uri="http://example.org/concepts/test",
            created_at=now,
            updated_at=now,
            broader=[],
        )
        assert concept.id == concept_id
        assert concept.scheme_id == scheme_id
        assert concept.pref_label == "Test Concept"
        assert concept.broader == []

    def test_concept_read_with_broader(self) -> None:
        """Test reading a concept with broader concepts."""
        now = datetime.now()
        broader_id = uuid4()
        scheme_id = uuid4()

        broader_concept = ConceptBrief(
            id=broader_id,
            scheme_id=scheme_id,
            pref_label="Broader Concept",
            definition=None,
            scope_note=None,
            uri=None,
            created_at=now,
            updated_at=now,
        )

        concept = ConceptRead(
            id=uuid4(),
            scheme_id=scheme_id,
            pref_label="Narrower Concept",
            definition=None,
            scope_note=None,
            uri=None,
            created_at=now,
            updated_at=now,
            broader=[broader_concept],
        )

        assert len(concept.broader) == 1
        assert concept.broader[0].pref_label == "Broader Concept"

    def test_concept_read_requires_all_fields(self) -> None:
        """Test that required fields must be provided."""
        with pytest.raises(ValidationError):
            ConceptRead()  # type: ignore[call-arg]

    def test_concept_read_optional_fields_can_be_none(self) -> None:
        """Test that optional fields can be None."""
        now = datetime.now()
        concept = ConceptRead(
            id=uuid4(),
            scheme_id=uuid4(),
            pref_label="Minimal",
            definition=None,
            scope_note=None,
            uri=None,
            created_at=now,
            updated_at=now,
            broader=[],
        )
        assert concept.definition is None
        assert concept.scope_note is None
        assert concept.uri is None
