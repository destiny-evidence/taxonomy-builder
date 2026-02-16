"""Tests for snapshot Pydantic schemas."""

from uuid import UUID

import pytest
from pydantic import ValidationError

from taxonomy_builder.schemas.snapshot import (
    SnapshotProjectMetadata,
    SnapshotClass,
    SnapshotConcept,
    SnapshotProperty,
    SnapshotScheme,
    SnapshotVocabulary,
)


def _concept(**overrides) -> dict:
    defaults = {
        "id": "00000000-0000-0000-0000-000000000001",
        "identifier": "c1",
        "uri": "http://example.org/c1",
        "pref_label": "Concept One",
    }
    return {**defaults, **overrides}


def _scheme(**overrides) -> dict:
    defaults = {
        "id": "00000000-0000-0000-0000-000000000010",
        "title": "Test Scheme",
    }
    return {**defaults, **overrides}


def _property(**overrides) -> dict:
    defaults = {
        "id": "00000000-0000-0000-0000-000000000020",
        "identifier": "prop1",
        "uri": "http://example.org/prop1",
        "label": "Property One",
        "domain_class": "http://example.org/Class",
        "range_datatype": "xsd:string",
        "cardinality": "single",
        "required": False,
    }
    return {**defaults, **overrides}


def _snapshot(**overrides) -> dict:
    defaults = {
        "project": {
            "id": "00000000-0000-0000-0000-000000000099",
            "name": "Test Project",
        },
    }
    return {**defaults, **overrides}


class TestSnapshotConcept:
    def test_valid(self) -> None:
        c = SnapshotConcept(**_concept())
        assert c.pref_label == "Concept One"
        assert c.id == UUID("00000000-0000-0000-0000-000000000001")
        assert c.alt_labels == []
        assert c.broader_ids == []
        assert c.related_ids == []

    def test_defaults(self) -> None:
        c = SnapshotConcept(**_concept())
        assert c.definition is None
        assert c.scope_note is None
        assert c.alt_labels == []
        assert c.broader_ids == []
        assert c.related_ids == []

    def test_nullable_fields(self) -> None:
        c = SnapshotConcept(**_concept(identifier=None, uri=None))
        assert c.identifier is None
        assert c.uri is None

    def test_missing_required_field(self) -> None:
        data = _concept()
        del data["pref_label"]
        with pytest.raises(ValidationError):
            SnapshotConcept(**data)


class TestSnapshotScheme:
    def test_valid_with_concepts(self) -> None:
        s = SnapshotScheme(**_scheme(concepts=[_concept()]))
        assert len(s.concepts) == 1
        assert s.concepts[0].pref_label == "Concept One"

    def test_defaults(self) -> None:
        s = SnapshotScheme(**_scheme())
        assert s.description is None
        assert s.uri is None
        assert s.concepts == []


class TestSnapshotProperty:
    def test_with_range_scheme(self) -> None:
        p = SnapshotProperty(
            **_property(
                range_scheme_id="00000000-0000-0000-0000-000000000010",
                range_scheme_uri="http://example.org/scheme",
                range_datatype=None,
            )
        )
        assert p.range_scheme_id == UUID("00000000-0000-0000-0000-000000000010")
        assert p.range_scheme_uri == "http://example.org/scheme"
        assert p.range_datatype is None

    def test_with_range_datatype(self) -> None:
        p = SnapshotProperty(**_property())
        assert p.range_scheme_id is None
        assert p.range_scheme_uri is None
        assert p.range_datatype == "xsd:string"

    def test_defaults(self) -> None:
        p = SnapshotProperty(**_property())
        assert p.description is None
        assert p.range_scheme_id is None
        assert p.range_scheme_uri is None


class TestSnapshotClass:
    def test_valid(self) -> None:
        c = SnapshotClass(uri="http://example.org/C", label="C", description="A class")
        assert c.uri == "http://example.org/C"

    def test_nullable_description(self) -> None:
        c = SnapshotClass(uri="http://example.org/C", label="C")
        assert c.description is None


class TestSnapshotProjectMetadata:
    def test_valid(self) -> None:
        p = SnapshotProjectMetadata(
            id="00000000-0000-0000-0000-000000000099", name="Test"
        )
        assert p.id == UUID("00000000-0000-0000-0000-000000000099")
        assert p.name == "Test"

    def test_defaults(self) -> None:
        p = SnapshotProjectMetadata(
            id="00000000-0000-0000-0000-000000000099", name="Test"
        )
        assert p.description is None
        assert p.namespace is None


class TestSnapshotVocabulary:
    def test_empty_snapshot(self) -> None:
        s = SnapshotVocabulary(**_snapshot())
        assert s.project.name == "Test Project"
        assert s.concept_schemes == []
        assert s.properties == []
        assert s.classes == []

    def test_full_snapshot(self) -> None:
        s = SnapshotVocabulary(
            **_snapshot(
                concept_schemes=[_scheme(concepts=[_concept()])],
                properties=[_property()],
                classes=[{"uri": "http://example.org/C", "label": "C"}],
            )
        )
        assert len(s.concept_schemes) == 1
        assert len(s.concept_schemes[0].concepts) == 1
        assert len(s.properties) == 1
        assert len(s.classes) == 1

    def test_round_trip(self) -> None:
        """model_dump -> model_validate produces identical result."""
        original = SnapshotVocabulary(
            **_snapshot(
                concept_schemes=[_scheme(concepts=[_concept()])],
                properties=[_property()],
                classes=[{"uri": "http://example.org/C", "label": "C"}],
            )
        )
        raw = original.model_dump(mode="json")
        restored = SnapshotVocabulary.model_validate(raw)
        assert restored == original

    def test_missing_project_fails(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotVocabulary(concept_schemes=[], properties=[], classes=[])
