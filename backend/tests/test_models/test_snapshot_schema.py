"""Tests for snapshot Pydantic schemas."""

from uuid import UUID

import pytest
from faker import Faker
from pydantic import ValidationError

from taxonomy_builder.schemas.snapshot import (
    SnapshotClass,
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotProperty,
    SnapshotScheme,
    SnapshotVocabulary,
)

fake = Faker()


def _concept(**overrides) -> dict:
    defaults = {
        "id": str(fake.uuid4()),
        "identifier": fake.slug(),
        "uri": fake.uri(),
        "pref_label": fake.sentence(nb_words=2),
    }
    return {**defaults, **overrides}


def _scheme(**overrides) -> dict:
    defaults = {
        "id": str(fake.uuid4()),
        "title": fake.sentence(nb_words=3),
    }
    return {**defaults, **overrides}


def _property(**overrides) -> dict:
    defaults = {
        "id": str(fake.uuid4()),
        "identifier": fake.slug(),
        "uri": fake.uri(),
        "label": fake.sentence(nb_words=2),
        "domain_class": fake.uri(),
        "range_datatype": "xsd:string",
        "cardinality": fake.random_element(["single", "multiple"]),
        "required": fake.boolean(),
    }
    return {**defaults, **overrides}


def _snapshot(**overrides) -> dict:
    defaults = {
        "project": {
            "id": str(fake.uuid4()),
            "name": fake.company(),
        },
    }
    return {**defaults, **overrides}


class TestSnapshotConcept:
    def test_valid(self) -> None:
        data = _concept()
        c = SnapshotConcept(**data)
        assert c.pref_label == data["pref_label"]
        assert c.id == UUID(data["id"])

    def test_missing_required_field(self) -> None:
        data = _concept()
        del data["pref_label"]
        with pytest.raises(ValidationError):
            SnapshotConcept(**data)


class TestSnapshotScheme:
    def test_valid_with_concepts(self) -> None:
        concept_data = _concept()
        s = SnapshotScheme(**_scheme(concepts=[concept_data]))
        assert len(s.concepts) == 1
        assert s.concepts[0].pref_label == concept_data["pref_label"]


class TestSnapshotProperty:
    def test_with_range_scheme(self) -> None:
        scheme_id = str(fake.uuid4())
        scheme_uri = fake.uri()
        p = SnapshotProperty(
            **_property(
                range_scheme_id=scheme_id,
                range_scheme_uri=scheme_uri,
                range_datatype=None,
            )
        )
        assert p.range_scheme_id == UUID(scheme_id)
        assert p.range_scheme_uri == scheme_uri
        assert p.range_datatype is None

    def test_with_range_datatype(self) -> None:
        p = SnapshotProperty(**_property())
        assert p.range_scheme_id is None
        assert p.range_datatype == "xsd:string"


class TestSnapshotClass:
    def test_valid(self) -> None:
        uri = fake.uri()
        c = SnapshotClass(uri=uri, label="C", description="A class")
        assert c.uri == uri


class TestSnapshotProjectMetadata:
    def test_valid(self) -> None:
        pid = str(fake.uuid4())
        name = fake.company()
        p = SnapshotProjectMetadata(id=pid, name=name)
        assert p.id == UUID(pid)
        assert p.name == name


class TestSnapshotVocabulary:
    def test_empty_snapshot(self) -> None:
        data = _snapshot()
        s = SnapshotVocabulary(**data)
        assert s.project.name == data["project"]["name"]
        assert s.concept_schemes == []
        assert s.properties == []
        assert s.classes == []

    def test_full_snapshot(self) -> None:
        s = SnapshotVocabulary(
            **_snapshot(
                concept_schemes=[_scheme(concepts=[_concept()])],
                properties=[_property()],
                classes=[{"uri": fake.uri(), "label": "C"}],
            )
        )
        assert len(s.concept_schemes) == 1
        assert len(s.concept_schemes[0].concepts) == 1
        assert len(s.properties) == 1
        assert len(s.classes) == 1

    def test_missing_project_fails(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotVocabulary(concept_schemes=[], properties=[], classes=[])
