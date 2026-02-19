"""Tests for snapshot validation via Pydantic validators."""

from uuid import UUID, uuid4

from taxonomy_builder.schemas.snapshot import (
    SnapshotClass,
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotProperty,
    SnapshotScheme,
    SnapshotVocabulary,
)
from taxonomy_builder.services.snapshot_service import validate_snapshot


def _project_meta() -> SnapshotProjectMetadata:
    return SnapshotProjectMetadata(id=uuid4(), name="Test")


def _vocab(
    *schemes: SnapshotScheme,
    properties: list[SnapshotProperty] | None = None,
    classes: list[SnapshotClass] | None = None,
) -> SnapshotVocabulary:
    return SnapshotVocabulary.model_construct(
        project=_project_meta(),
        concept_schemes=list(schemes),
        properties=properties or [],
        classes=classes or [],
    )


def _scheme(
    title: str = "Scheme",
    *,
    id: UUID | None = None,
    uri: str | None = "http://example.org/scheme",
    concepts: list[SnapshotConcept] | None = None,
) -> SnapshotScheme:
    return SnapshotScheme.model_construct(
        id=id or uuid4(),
        title=title,
        uri=uri,
        concepts=concepts or [],
    )


def _concept(
    pref_label: str = "Term",
    *,
    id: UUID | None = None,
    uri: str | None = "http://example.org/concept/term",
    broader_ids: list[UUID] | None = None,
    related_ids: list[UUID] | None = None,
) -> SnapshotConcept:
    return SnapshotConcept.model_construct(
        id=id or uuid4(),
        pref_label=pref_label,
        uri=uri,
        broader_ids=broader_ids or [],
        related_ids=related_ids or [],
    )


class TestValidProject:
    def test_valid_project(self) -> None:
        concept = _concept("Term A")
        scheme = _scheme("Test Scheme", concepts=[concept])
        result = validate_snapshot(_vocab(scheme))
        assert result.valid is True
        assert result.errors == []


class TestNoSchemes:
    def test_no_schemes(self) -> None:
        result = validate_snapshot(_vocab())
        assert result.valid is False
        assert any(e.code == "no_schemes" for e in result.errors)


class TestNoConceptsInScheme:
    def test_scheme_with_no_concepts(self) -> None:
        scheme = _scheme("Empty Scheme", concepts=[])
        result = validate_snapshot(_vocab(scheme))
        assert result.valid is False
        assert any(e.code == "scheme_no_concepts" for e in result.errors)


class TestSchemeMissingUri:
    def test_scheme_missing_uri(self) -> None:
        scheme_id = uuid4()
        scheme = _scheme("No URI", id=scheme_id, uri=None, concepts=[_concept()])
        result = validate_snapshot(_vocab(scheme))
        assert result.valid is False
        uri_errors = [e for e in result.errors if e.code == "scheme_missing_uri"]
        assert len(uri_errors) == 1
        assert uri_errors[0].entity_id == scheme_id
        assert uri_errors[0].entity_label == "No URI"


class TestConceptMissingUri:
    def test_concept_with_no_uri(self) -> None:
        concept_id = uuid4()
        concept = _concept("No URI", id=concept_id, uri=None)
        scheme = _scheme(concepts=[concept])
        result = validate_snapshot(_vocab(scheme))
        assert result.valid is False
        uri_errors = [e for e in result.errors if e.code == "concept_missing_uri"]
        assert len(uri_errors) == 1
        assert uri_errors[0].entity_id == concept_id


class TestConceptMissingPrefLabel:
    def test_whitespace_only_label(self) -> None:
        scheme = _scheme(concepts=[_concept("   ")])
        result = validate_snapshot(_vocab(scheme))
        assert result.valid is False
        assert any(e.code == "concept_missing_pref_label" for e in result.errors)


class TestCollectsAllErrors:
    def test_multiple_errors_collected(self) -> None:
        """Validation returns all errors, not just the first one."""
        scheme = _scheme("Bad", uri=None, concepts=[_concept("  ")])
        result = validate_snapshot(_vocab(scheme))
        assert result.valid is False
        codes = {e.code for e in result.errors}
        assert "scheme_missing_uri" in codes
        assert "concept_missing_pref_label" in codes


class TestMixedValidity:
    def test_one_valid_one_invalid_scheme(self) -> None:
        good = _scheme("Good", concepts=[_concept("Valid")])
        bad_id = uuid4()
        bad = _scheme("Bad", id=bad_id, uri=None, concepts=[_concept("Also Valid")])
        result = validate_snapshot(_vocab(good, bad))
        assert result.valid is False
        uri_errors = [e for e in result.errors if e.code == "scheme_missing_uri"]
        assert len(uri_errors) == 1
        assert uri_errors[0].entity_id == bad_id


class TestBrokenBroaderRef:
    def test_broader_referencing_nonexistent_concept(self) -> None:
        orphan_id = uuid4()
        concept_a = _concept("A", broader_ids=[orphan_id])
        scheme = _scheme(concepts=[concept_a])
        result = validate_snapshot(_vocab(scheme))
        assert result.valid is False
        errors = [e for e in result.errors if e.code == "broken_broader_ref"]
        assert len(errors) == 1
        assert errors[0].entity_id == concept_a.id

    def test_valid_broader_ref_passes(self) -> None:
        parent = _concept("Parent")
        child = _concept("Child", broader_ids=[parent.id])
        scheme = _scheme(concepts=[parent, child])
        result = validate_snapshot(_vocab(scheme))
        assert result.valid is True


class TestBrokenRelatedRef:
    def test_related_referencing_nonexistent_concept(self) -> None:
        orphan_id = uuid4()
        concept_a = _concept("A", related_ids=[orphan_id])
        scheme = _scheme(concepts=[concept_a])
        result = validate_snapshot(_vocab(scheme))
        assert result.valid is False
        errors = [e for e in result.errors if e.code == "broken_related_ref"]
        assert len(errors) == 1
        assert errors[0].entity_id == concept_a.id


def _class(
    label: str = "MyClass",
    *,
    id: UUID | None = None,
    identifier: str = "myclass",
    uri: str | None = "http://example.org/class/myclass",
) -> SnapshotClass:
    return SnapshotClass.model_construct(
        id=id or uuid4(),
        identifier=identifier,
        uri=uri,
        label=label,
    )


class TestPropertyMissingRangeSchemeUri:
    def test_range_scheme_id_without_uri(self) -> None:
        cls = _class("Class", uri="http://example.org/Class")
        prop = SnapshotProperty.model_construct(
            id=uuid4(),
            identifier="prop1",
            uri="http://example.org/prop1",
            label="Test Property",
            domain_class="http://example.org/Class",
            range_scheme_id=uuid4(),
            range_scheme_uri=None,
            cardinality="one",
            required=False,
        )
        scheme = _scheme(concepts=[_concept("Term")])
        result = validate_snapshot(_vocab(scheme, properties=[prop], classes=[cls]))
        assert result.valid is False
        errors = [e for e in result.errors if e.code == "property_missing_range_scheme_uri"]
        assert len(errors) == 1
        assert errors[0].entity_id == prop.id


class TestBrokenRangeSchemeRef:
    def test_property_referencing_nonexistent_scheme(self) -> None:
        orphan_scheme_id = uuid4()
        cls = _class("Class", uri="http://example.org/Class")
        prop = SnapshotProperty.model_construct(
            id=uuid4(),
            identifier="prop1",
            uri="http://example.org/prop1",
            label="Test Property",
            domain_class="http://example.org/Class",
            range_scheme_id=orphan_scheme_id,
            range_scheme_uri="http://example.org/orphan",
            cardinality="one",
            required=False,
        )
        concept = _concept("Term")
        scheme = _scheme(concepts=[concept])
        result = validate_snapshot(_vocab(scheme, properties=[prop], classes=[cls]))
        assert result.valid is False
        errors = [e for e in result.errors if e.code == "broken_range_scheme_ref"]
        assert len(errors) == 1
        assert errors[0].entity_id == prop.id

    def test_valid_range_scheme_ref_passes(self) -> None:
        cls = _class("Class", uri="http://example.org/Class")
        scheme = _scheme(concepts=[_concept("Term")])
        prop = SnapshotProperty.model_construct(
            id=uuid4(),
            identifier="prop1",
            uri="http://example.org/prop1",
            label="Test Property",
            domain_class="http://example.org/Class",
            range_scheme_id=scheme.id,
            range_scheme_uri="http://example.org/scheme",
            cardinality="one",
            required=False,
        )
        result = validate_snapshot(_vocab(scheme, properties=[prop], classes=[cls]))
        assert result.valid is True

    def test_null_range_scheme_passes(self) -> None:
        cls = _class("Class", uri="http://example.org/Class")
        prop = SnapshotProperty.model_construct(
            id=uuid4(),
            identifier="prop1",
            uri="http://example.org/prop1",
            label="Test Property",
            domain_class="http://example.org/Class",
            range_scheme_id=None,
            range_datatype="xsd:string",
            cardinality="one",
            required=False,
        )
        scheme = _scheme(concepts=[_concept("Term")])
        result = validate_snapshot(_vocab(scheme, properties=[prop], classes=[cls]))
        assert result.valid is True


class TestClassMissingUri:
    def test_class_missing_uri(self) -> None:
        class_id = uuid4()
        cls = _class("No URI", id=class_id, uri=None)
        scheme = _scheme(concepts=[_concept()])
        result = validate_snapshot(_vocab(scheme, classes=[cls]))
        assert result.valid is False
        uri_errors = [e for e in result.errors if e.code == "class_missing_uri"]
        assert len(uri_errors) == 1
        assert uri_errors[0].entity_id == class_id
        assert uri_errors[0].entity_label == "No URI"


class TestClassMissingLabel:
    def test_whitespace_only_label(self) -> None:
        cls = _class("   ")
        scheme = _scheme(concepts=[_concept()])
        result = validate_snapshot(_vocab(scheme, classes=[cls]))
        assert result.valid is False
        assert any(e.code == "class_missing_label" for e in result.errors)


class TestBrokenDomainClassRef:
    def test_property_domain_class_not_in_classes(self) -> None:
        prop = SnapshotProperty.model_construct(
            id=uuid4(),
            identifier="prop1",
            uri="http://example.org/prop1",
            label="Test Property",
            domain_class="http://example.org/NonExistent",
            range_datatype="xsd:string",
            cardinality="one",
            required=False,
        )
        cls = _class("MyClass", uri="http://example.org/class/myclass")
        concept = _concept("Term")
        scheme = _scheme(concepts=[concept])
        result = validate_snapshot(_vocab(scheme, properties=[prop], classes=[cls]))
        assert result.valid is False
        errors = [e for e in result.errors if e.code == "broken_domain_class_ref"]
        assert len(errors) == 1
        assert errors[0].entity_id == prop.id

    def test_valid_domain_class_ref_passes(self) -> None:
        cls = _class("MyClass", uri="http://example.org/Class")
        prop = SnapshotProperty.model_construct(
            id=uuid4(),
            identifier="prop1",
            uri="http://example.org/prop1",
            label="Test Property",
            domain_class="http://example.org/Class",
            range_datatype="xsd:string",
            cardinality="one",
            required=False,
        )
        concept = _concept("Term")
        scheme = _scheme(concepts=[concept])
        result = validate_snapshot(_vocab(scheme, properties=[prop], classes=[cls]))
        assert result.valid is True
