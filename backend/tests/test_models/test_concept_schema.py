"""Tests for Concept Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from faker import Faker
from pydantic import ValidationError

from taxonomy_builder.schemas.concept import (
    ConceptBrief,
    ConceptCreate,
    ConceptRead,
    ConceptUpdate,
)

fake = Faker()


class TestConceptCreate:
    """Tests for ConceptCreate schema."""

    def test_valid_concept_create(self) -> None:
        """Test creating a valid concept."""
        label = fake.sentence(nb_words=2)
        identifier = fake.slug()
        definition = fake.sentence()
        scope_note = fake.sentence()
        concept = ConceptCreate(
            pref_label=label,
            identifier=identifier,
            definition=definition,
            scope_note=scope_note,
        )
        assert concept.pref_label == label
        assert concept.identifier == identifier
        assert concept.definition == definition
        assert concept.scope_note == scope_note

    def test_concept_create_pref_label_only(self) -> None:
        """Test creating a concept with only pref_label."""
        label = fake.sentence(nb_words=2)
        concept = ConceptCreate(pref_label=label)
        assert concept.pref_label == label
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
        label = fake.sentence(nb_words=2)
        concept = ConceptUpdate(pref_label=label)
        assert concept.pref_label == label

    def test_concept_update_with_all_fields(self) -> None:
        """Test updating all fields."""
        label = fake.sentence(nb_words=2)
        identifier = fake.slug()
        definition = fake.sentence()
        scope_note = fake.sentence()
        concept = ConceptUpdate(
            pref_label=label,
            identifier=identifier,
            definition=definition,
            scope_note=scope_note,
        )
        assert concept.pref_label == label
        assert concept.identifier == identifier
        assert concept.definition == definition
        assert concept.scope_note == scope_note

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
        identifier = fake.slug()
        label = fake.sentence(nb_words=2)
        definition = fake.sentence()
        scope_note = fake.sentence()
        uri = fake.uri()
        concept = ConceptRead(
            id=concept_id,
            scheme_id=scheme_id,
            identifier=identifier,
            pref_label=label,
            definition=definition,
            scope_note=scope_note,
            uri=uri,
            created_at=now,
            updated_at=now,
            broader=[],
        )
        assert concept.id == concept_id
        assert concept.scheme_id == scheme_id
        assert concept.identifier == identifier
        assert concept.pref_label == label
        assert concept.broader == []

    def test_concept_read_with_broader(self) -> None:
        """Test reading a concept with broader concepts."""
        now = datetime.now()
        scheme_id = fake.uuid4()
        broader_label = fake.sentence(nb_words=2)

        broader_concept = ConceptBrief(
            id=fake.uuid4(),
            scheme_id=scheme_id,
            identifier=fake.slug(),
            pref_label=broader_label,
            definition=None,
            scope_note=None,
            uri=None,
            created_at=now,
            updated_at=now,
        )

        concept = ConceptRead(
            id=fake.uuid4(),
            scheme_id=scheme_id,
            identifier=fake.slug(),
            pref_label=fake.sentence(nb_words=2),
            definition=None,
            scope_note=None,
            uri=None,
            created_at=now,
            updated_at=now,
            broader=[broader_concept],
        )

        assert len(concept.broader) == 1
        assert concept.broader[0].pref_label == broader_label

    def test_concept_read_requires_all_fields(self) -> None:
        """Test that required fields must be provided."""
        with pytest.raises(ValidationError):
            ConceptRead()  # type: ignore[call-arg]

    def test_concept_read_optional_fields_can_be_none(self) -> None:
        """Test that optional fields can be None."""
        now = datetime.now()
        concept = ConceptRead(
            id=fake.uuid4(),
            scheme_id=fake.uuid4(),
            identifier=None,
            pref_label=fake.sentence(nb_words=2),
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
        alt1 = fake.word()
        alt2 = fake.word()
        concept = ConceptCreate(
            pref_label=fake.sentence(nb_words=2),
            alt_labels=[alt1, alt2],
        )
        assert concept.alt_labels == [alt1, alt2]

    def test_concept_create_alt_labels_default_empty(self) -> None:
        """Test that alt_labels defaults to empty list."""
        concept = ConceptCreate(pref_label=fake.sentence(nb_words=2))
        assert concept.alt_labels == []

    def test_concept_create_alt_labels_empty_list(self) -> None:
        """Test creating concept with explicit empty alt_labels."""
        concept = ConceptCreate(pref_label=fake.sentence(nb_words=2), alt_labels=[])
        assert concept.alt_labels == []

    def test_concept_create_alt_labels_strips_whitespace(self) -> None:
        """Test that alt labels are stripped of whitespace."""
        concept = ConceptCreate(
            pref_label=fake.sentence(nb_words=2),
            alt_labels=["  padded  ", "normal"],
        )
        assert concept.alt_labels == ["padded", "normal"]

    def test_concept_create_alt_labels_removes_empty_strings(self) -> None:
        """Test that empty alt labels are filtered out."""
        concept = ConceptCreate(
            pref_label=fake.sentence(nb_words=2),
            alt_labels=["valid", "", "  ", "also valid"],
        )
        assert concept.alt_labels == ["valid", "also valid"]

    def test_concept_create_alt_labels_removes_duplicates(self) -> None:
        """Test that duplicate alt labels are removed (case-insensitive)."""
        concept = ConceptCreate(
            pref_label=fake.sentence(nb_words=2),
            alt_labels=["Canine", "canine", "CANINE", "Dog"],
        )
        # Should keep first occurrence of case-insensitive duplicates
        assert concept.alt_labels == ["Canine", "Dog"]


class TestConceptUpdateAltLabels:
    """Tests for alt_labels in ConceptUpdate schema."""

    def test_concept_update_with_alt_labels(self) -> None:
        """Test updating concept with alt labels."""
        alt1 = fake.word()
        alt2 = fake.word()
        concept = ConceptUpdate(alt_labels=[alt1, alt2])
        assert concept.alt_labels == [alt1, alt2]

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
        alt = fake.word()
        concept = ConceptRead(
            id=fake.uuid4(),
            scheme_id=fake.uuid4(),
            identifier=fake.slug(),
            pref_label=fake.sentence(nb_words=2),
            definition=None,
            scope_note=None,
            uri=None,
            alt_labels=[alt],
            created_at=now,
            updated_at=now,
            broader=[],
        )
        assert concept.alt_labels == [alt]

    def test_concept_read_alt_labels_defaults_empty(self) -> None:
        """Test that alt_labels defaults to empty list in read."""
        now = datetime.now()
        concept = ConceptRead(
            id=fake.uuid4(),
            scheme_id=fake.uuid4(),
            identifier=fake.slug(),
            pref_label=fake.sentence(nb_words=2),
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
        alt1 = fake.word()
        alt2 = fake.word()
        concept = ConceptBrief(
            id=fake.uuid4(),
            scheme_id=fake.uuid4(),
            identifier=fake.slug(),
            pref_label=fake.sentence(nb_words=2),
            definition=None,
            scope_note=None,
            uri=None,
            alt_labels=[alt1, alt2],
            created_at=now,
            updated_at=now,
        )
        assert concept.alt_labels == [alt1, alt2]

    def test_concept_brief_alt_labels_defaults_empty(self) -> None:
        """Test that alt_labels defaults to empty list in brief."""
        now = datetime.now()
        concept = ConceptBrief(
            id=fake.uuid4(),
            scheme_id=fake.uuid4(),
            identifier=fake.slug(),
            pref_label=fake.sentence(nb_words=2),
            definition=None,
            scope_note=None,
            uri=None,
            created_at=now,
            updated_at=now,
        )
        assert concept.alt_labels == []
