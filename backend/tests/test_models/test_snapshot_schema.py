"""Tests for snapshot Pydantic schemas."""

from uuid import UUID

import pytest
from pydantic import ValidationError

from taxonomy_builder.schemas.snapshot import (
    SnapshotClass,
    SnapshotConcept,
    SnapshotProjectMetadata,
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
        "uri": "http://example.org/scheme",
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
            "namespace": "http://example.org/",
        },
    }
    return {**defaults, **overrides}


class TestSnapshotConcept:
    def test_valid(self) -> None:
        c = SnapshotConcept(**_concept())
        assert c.pref_label == "Concept One"
        assert c.id == UUID("00000000-0000-0000-0000-000000000001")

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
        assert p.range_datatype == "xsd:string"
        assert p.range_class is None

    def test_with_range_class(self) -> None:
        p = SnapshotProperty(
            **_property(
                range_datatype=None,
                range_class="http://example.org/OtherClass",
            )
        )
        assert p.range_scheme_id is None
        assert p.range_datatype is None
        assert p.range_class == "http://example.org/OtherClass"

    def test_multiple_range_fields_raises(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotProperty(
                **_property(
                    range_scheme_id="00000000-0000-0000-0000-000000000010",
                    range_datatype="xsd:string",
                )
            )

    def test_no_range_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotProperty(
                **_property(range_scheme_id=None, range_datatype=None)
            )

    def test_range_scheme_id_without_uri_raises(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotProperty(
                **_property(
                    range_scheme_id="00000000-0000-0000-0000-000000000010",
                    range_scheme_uri=None,
                    range_datatype=None,
                )
            )


class TestSnapshotClass:
    def test_valid(self) -> None:
        c = SnapshotClass(
            id="00000000-0000-0000-0000-000000000030",
            identifier="MyClass",
            uri="http://example.org/C",
            label="C",
            description="A class",
            scope_note="Use for testing",
        )
        assert c.uri == "http://example.org/C"
        assert c.id == UUID("00000000-0000-0000-0000-000000000030")
        assert c.identifier == "MyClass"
        assert c.scope_note == "Use for testing"

    def test_missing_uri_raises(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotClass(
                id="00000000-0000-0000-0000-000000000030",
                identifier="MyClass",
                uri=None,
                label="C",
            )

    def test_empty_label_raises(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotClass(
                id="00000000-0000-0000-0000-000000000030",
                identifier="MyClass",
                uri="http://example.org/C",
                label="   ",
            )


class TestSnapshotProjectMetadata:
    def test_valid(self) -> None:
        p = SnapshotProjectMetadata(
            id="00000000-0000-0000-0000-000000000099",
            name="Test",
            namespace="http://example.org/",
        )
        assert p.id == UUID("00000000-0000-0000-0000-000000000099")
        assert p.name == "Test"


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
                classes=[{
                    "id": "00000000-0000-0000-0000-000000000030",
                    "identifier": "C",
                    "uri": "http://example.org/C",
                    "label": "C",
                }],
            )
        )
        assert len(s.concept_schemes) == 1
        assert len(s.concept_schemes[0].concepts) == 1
        assert len(s.properties) == 1
        assert len(s.classes) == 1

    def test_missing_project_fails(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotVocabulary(concept_schemes=[], properties=[], classes=[])
