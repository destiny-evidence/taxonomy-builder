"""Tests for snapshot Pydantic schemas."""

from uuid import uuid4

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


class TestSnapshotConcept:
    def test_valid(self) -> None:
        concept = SnapshotConcept(
            id=fake.uuid4(),
            identifier=fake.slug(),
            uri=fake.uri(),
            pref_label=fake.sentence(nb_words=2),
        )
        assert concept.pref_label
        assert concept.id

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotConcept(
                id=fake.uuid4(),
                identifier=fake.slug(),
                uri=fake.uri(),
            )


class TestSnapshotScheme:
    def test_valid_with_concepts(self) -> None:
        label = fake.sentence(nb_words=2)
        scheme = SnapshotScheme(
            id=fake.uuid4(),
            title=fake.sentence(nb_words=3),
            concepts=[
                {
                    "id": str(fake.uuid4()),
                    "identifier": fake.slug(),
                    "uri": fake.uri(),
                    "pref_label": label,
                }
            ],
        )
        assert len(scheme.concepts) == 1
        assert scheme.concepts[0].pref_label == label


class TestSnapshotProperty:
    def test_with_range_scheme(self) -> None:
        scheme_id = uuid4()
        scheme_uri = fake.uri()
        prop = SnapshotProperty(
            id=fake.uuid4(),
            identifier=fake.slug(),
            uri=fake.uri(),
            label=fake.sentence(nb_words=2),
            domain_class=fake.uri(),
            range_scheme_id=scheme_id,
            range_scheme_uri=scheme_uri,
            range_datatype=None,
            cardinality=fake.random_element(["single", "multiple"]),
            required=fake.boolean(),
        )
        assert prop.range_scheme_id == scheme_id
        assert prop.range_scheme_uri == scheme_uri
        assert prop.range_datatype is None

    def test_with_range_datatype(self) -> None:
        prop = SnapshotProperty(
            id=fake.uuid4(),
            identifier=fake.slug(),
            uri=fake.uri(),
            label=fake.sentence(nb_words=2),
            domain_class=fake.uri(),
            range_datatype="xsd:string",
            cardinality=fake.random_element(["single", "multiple"]),
            required=fake.boolean(),
        )
        assert prop.range_scheme_id is None
        assert prop.range_datatype == "xsd:string"


class TestSnapshotClass:
    def test_valid(self) -> None:
        uri = fake.uri()
        label = fake.sentence(nb_words=2)
        cls = SnapshotClass(uri=uri, label=label, description=fake.sentence())
        assert cls.uri == uri
        assert cls.label == label


class TestSnapshotProjectMetadata:
    def test_valid(self) -> None:
        name = fake.company()
        meta = SnapshotProjectMetadata(id=fake.uuid4(), name=name)
        assert meta.name == name
        assert meta.id


class TestSnapshotVocabulary:
    def test_empty_snapshot(self) -> None:
        name = fake.company()
        snapshot = SnapshotVocabulary(
            project={"id": str(fake.uuid4()), "name": name},
        )
        assert snapshot.project.name == name
        assert snapshot.concept_schemes == []
        assert snapshot.properties == []
        assert snapshot.classes == []

    def test_full_snapshot(self) -> None:
        snapshot = SnapshotVocabulary(
            project={"id": str(fake.uuid4()), "name": fake.company()},
            concept_schemes=[
                {
                    "id": str(fake.uuid4()),
                    "title": fake.sentence(nb_words=3),
                    "concepts": [
                        {
                            "id": str(fake.uuid4()),
                            "identifier": fake.slug(),
                            "uri": fake.uri(),
                            "pref_label": fake.sentence(nb_words=2),
                        }
                    ],
                }
            ],
            properties=[
                {
                    "id": str(fake.uuid4()),
                    "identifier": fake.slug(),
                    "uri": fake.uri(),
                    "label": fake.sentence(nb_words=2),
                    "domain_class": fake.uri(),
                    "range_datatype": "xsd:string",
                    "cardinality": "single",
                    "required": False,
                }
            ],
            classes=[{"uri": fake.uri(), "label": fake.sentence(nb_words=2)}],
        )
        assert len(snapshot.concept_schemes) == 1
        assert len(snapshot.concept_schemes[0].concepts) == 1
        assert len(snapshot.properties) == 1
        assert len(snapshot.classes) == 1

    def test_missing_project_fails(self) -> None:
        with pytest.raises(ValidationError):
            SnapshotVocabulary(concept_schemes=[], properties=[], classes=[])
