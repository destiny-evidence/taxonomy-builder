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
            identifier="test",
            definition="A test definition",
            scope_note="Use for testing",
        )
        assert concept.pref_label == "Test Concept"
        assert concept.identifier == "test"
        assert concept.definition == "A test definition"
        assert concept.scope_note == "Use for testing"

    def test_concept_create_pref_label_only(self) -> None:
        """Test creating a concept with only pref_label."""
        concept = ConceptCreate(pref_label="Minimal Concept")
        assert concept.pref_label == "Minimal Concept"
        assert concept.identifier is None
        assert concept.definition is None
        assert concept.scope_note is None

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
        assert concept.identifier is None
        assert concept.definition is None
        assert concept.scope_note is None

    def test_concept_update_with_pref_label(self) -> None:
        """Test updating with a new pref_label."""
        concept = ConceptUpdate(pref_label="New Label")
        assert concept.pref_label == "New Label"

    def test_concept_update_with_all_fields(self) -> None:
        """Test updating all fields."""
        concept = ConceptUpdate(
            pref_label="Updated Label",
            identifier="updated",
            definition="Updated definition",
            scope_note="Updated scope note",
        )
        assert concept.pref_label == "Updated Label"
        assert concept.identifier == "updated"
        assert concept.definition == "Updated definition"
        assert concept.scope_note == "Updated scope note"

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
            identifier="test",
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
        assert concept.identifier == "test"
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
            identifier="broader",
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
            identifier="narrower",
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
            identifier=None,
            pref_label="Minimal",
            definition=None,
            scope_note=None,
            uri=None,
            created_at=now,
            updated_at=now,
            broader=[],
        )
        assert concept.identifier is None
        assert concept.definition is None
        assert concept.scope_note is None
        assert concept.uri is None


class TestConceptCreateAltLabels:
    """Tests for alt_labels in ConceptCreate schema."""

    def test_concept_create_with_alt_labels(self) -> None:
        """Test creating a concept with alt labels."""
        concept = ConceptCreate(
            pref_label="Dogs",
            alt_labels=["Canines", "Domestic dogs"],
        )
        assert concept.alt_labels == ["Canines", "Domestic dogs"]

    def test_concept_create_alt_labels_default_empty(self) -> None:
        """Test that alt_labels defaults to empty list."""
        concept = ConceptCreate(pref_label="Test")
        assert concept.alt_labels == []

    def test_concept_create_alt_labels_empty_list(self) -> None:
        """Test creating concept with explicit empty alt_labels."""
        concept = ConceptCreate(pref_label="Test", alt_labels=[])
        assert concept.alt_labels == []

    def test_concept_create_alt_labels_strips_whitespace(self) -> None:
        """Test that alt labels are stripped of whitespace."""
        concept = ConceptCreate(
            pref_label="Test",
            alt_labels=["  padded  ", "normal"],
        )
        assert concept.alt_labels == ["padded", "normal"]

    def test_concept_create_alt_labels_removes_empty_strings(self) -> None:
        """Test that empty alt labels are filtered out."""
        concept = ConceptCreate(
            pref_label="Test",
            alt_labels=["valid", "", "  ", "also valid"],
        )
        assert concept.alt_labels == ["valid", "also valid"]

    def test_concept_create_alt_labels_removes_duplicates(self) -> None:
        """Test that duplicate alt labels are removed (case-insensitive)."""
        concept = ConceptCreate(
            pref_label="Test",
            alt_labels=["Canine", "canine", "CANINE", "Dog"],
        )
        # Should keep first occurrence of case-insensitive duplicates
        assert concept.alt_labels == ["Canine", "Dog"]


class TestConceptUpdateAltLabels:
    """Tests for alt_labels in ConceptUpdate schema."""

    def test_concept_update_with_alt_labels(self) -> None:
        """Test updating concept with alt labels."""
        concept = ConceptUpdate(alt_labels=["Synonym 1", "Synonym 2"])
        assert concept.alt_labels == ["Synonym 1", "Synonym 2"]

    def test_concept_update_alt_labels_none_by_default(self) -> None:
        """Test that alt_labels is None by default (no update)."""
        concept = ConceptUpdate()
        assert concept.alt_labels is None

    def test_concept_update_alt_labels_can_be_empty_list(self) -> None:
        """Test that alt_labels can be set to empty list (clear all)."""
        concept = ConceptUpdate(alt_labels=[])
        assert concept.alt_labels == []

    def test_concept_update_alt_labels_strips_whitespace(self) -> None:
        """Test that alt labels are stripped of whitespace."""
        concept = ConceptUpdate(alt_labels=["  padded  ", "normal"])
        assert concept.alt_labels == ["padded", "normal"]

    def test_concept_update_alt_labels_removes_empty_strings(self) -> None:
        """Test that empty alt labels are filtered out."""
        concept = ConceptUpdate(alt_labels=["valid", "", "  ", "also valid"])
        assert concept.alt_labels == ["valid", "also valid"]


class TestConceptReadAltLabels:
    """Tests for alt_labels in ConceptRead/ConceptBrief schemas."""

    def test_concept_read_includes_alt_labels(self) -> None:
        """Test that ConceptRead includes alt_labels field."""
        now = datetime.now()
        concept = ConceptRead(
            id=uuid4(),
            scheme_id=uuid4(),
            identifier="test",
            pref_label="Test",
            definition=None,
            scope_note=None,
            uri=None,
            alt_labels=["Synonym"],
            created_at=now,
            updated_at=now,
            broader=[],
        )
        assert concept.alt_labels == ["Synonym"]

    def test_concept_read_alt_labels_defaults_empty(self) -> None:
        """Test that alt_labels defaults to empty list in read."""
        now = datetime.now()
        concept = ConceptRead(
            id=uuid4(),
            scheme_id=uuid4(),
            identifier="test",
            pref_label="Test",
            definition=None,
            scope_note=None,
            uri=None,
            created_at=now,
            updated_at=now,
            broader=[],
        )
        assert concept.alt_labels == []

    def test_concept_brief_includes_alt_labels(self) -> None:
        """Test that ConceptBrief includes alt_labels field."""
        now = datetime.now()
        concept = ConceptBrief(
            id=uuid4(),
            scheme_id=uuid4(),
            identifier="test",
            pref_label="Test",
            definition=None,
            scope_note=None,
            uri=None,
            alt_labels=["Alt1", "Alt2"],
            created_at=now,
            updated_at=now,
        )
        assert concept.alt_labels == ["Alt1", "Alt2"]

    def test_concept_brief_alt_labels_defaults_empty(self) -> None:
        """Test that alt_labels defaults to empty list in brief."""
        now = datetime.now()
        concept = ConceptBrief(
            id=uuid4(),
            scheme_id=uuid4(),
            identifier="test",
            pref_label="Test",
            definition=None,
            scope_note=None,
            uri=None,
            created_at=now,
            updated_at=now,
        )
        assert concept.alt_labels == []
