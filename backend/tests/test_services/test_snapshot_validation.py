"""Tests for snapshot validation via Pydantic validators."""

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from taxonomy_builder.schemas.snapshot import (
    SnapshotClass,
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotProperty,
    SnapshotScheme,
    SnapshotVocabulary,
)
from taxonomy_builder.services.snapshot_service import validate_snapshot


# ---------------------------------------------------------------------------
# Lightweight stubs for ORM objects so we can test from_* factory methods
# without a database session.
# ---------------------------------------------------------------------------

def _stub_concept(**overrides):
    """Stub mimicking a Concept ORM instance for from_concept()."""
    defaults = dict(
        id=uuid4(),
        identifier="term",
        uri="http://example.org/term",
        pref_label="Term",
        definition=None,
        scope_note=None,
        alt_labels=[],
        broader=[],
        related=[],
    )
    return SimpleNamespace(**(defaults | overrides))


def _stub_property(**overrides):
    """Stub mimicking a Property ORM instance for from_property()."""
    defaults = dict(
        id=uuid4(),
        identifier="prop1",
        uri="http://example.org/prop1",
        label="Test Prop",
        description=None,
        domain_class="",
        domain_classes=[],
        range_datatype=None,
        range_scheme_id=None,
        range_scheme=None,
        range_class=None,
        cardinality="single",
        required=False,
    )
    return SimpleNamespace(**(defaults | overrides))


def _stub_ontology_class(**overrides):
    """Stub mimicking an OntologyClass ORM instance for from_class()."""
    defaults = dict(
        id=uuid4(),
        identifier="finding",
        uri="http://example.org/Finding",
        label="Finding",
        description=None,
        scope_note=None,
        superclasses=[],
    )
    return SimpleNamespace(**(defaults | overrides))


def _project_meta() -> SnapshotProjectMetadata:
    return SnapshotProjectMetadata(id=uuid4(), name="Test", namespace="http://example.org/")


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


class TestSnapshotClassSuperclassUris:
    """SnapshotClass should carry superclass_uris field."""

    def test_from_class_sets_empty_superclass_uris(self) -> None:
        """from_class() should set superclass_uris=[] when class has no superclasses."""
        cls = SnapshotClass.from_class(_stub_ontology_class())
        assert cls.superclass_uris == []

    def test_superclass_uris_in_snapshot(self) -> None:
        """superclass_uris should be present and validatable in a snapshot."""
        cls = _class("Finding", uri="http://example.org/Finding")
        cls.superclass_uris = ["http://example.org/Entity"]

        parent = _class("Entity", uri="http://example.org/Entity")
        scheme = _scheme(concepts=[_concept("Term")])
        result = validate_snapshot(_vocab(scheme, classes=[cls, parent]))
        assert result.valid is True

    def test_broken_superclass_ref(self) -> None:
        """superclass_uris referencing non-existent class should fail validation."""
        cls = _class("Finding", uri="http://example.org/Finding")
        cls.superclass_uris = ["http://example.org/NonExistent"]

        scheme = _scheme(concepts=[_concept("Term")])
        result = validate_snapshot(_vocab(scheme, classes=[cls]))
        assert result.valid is False
        errors = [e for e in result.errors if e.code == "broken_superclass_ref"]
        assert len(errors) == 1

    def test_well_known_superclass_uri_allowed(self) -> None:
        """Well-known URIs like skos:Concept should be allowed as superclass targets."""
        cls = _class("MyConcept", uri="http://example.org/MyConcept")
        cls.superclass_uris = ["http://www.w3.org/2004/02/skos/core#Concept"]

        scheme = _scheme(concepts=[_concept("Term")])
        result = validate_snapshot(_vocab(scheme, classes=[cls]))
        assert result.valid is True


class TestSnapshotConceptTypeUris:
    """SnapshotConcept should carry concept_type_uris field."""

    def test_from_concept_sets_empty_type_uris(self) -> None:
        """from_concept() should set concept_type_uris=[] by default."""
        concept = SnapshotConcept.from_concept(_stub_concept())
        assert concept.concept_type_uris == []


class TestSnapshotPropertyNewFields:
    """SnapshotProperty should carry property_type and domain_class_uris."""

    def test_domain_class_uris_wraps_scalar(self) -> None:
        """from_property() should wrap scalar domain_class in a list."""
        stub = _stub_property(
            domain_class="http://example.org/Class",
            range_datatype="xsd:string",
        )
        prop = SnapshotProperty.from_property(stub)
        assert prop.domain_class_uris == ["http://example.org/Class"]

    def test_property_type_inferred_datatype(self) -> None:
        """Properties with range_datatype should infer property_type='datatype'."""
        stub = _stub_property(range_datatype="xsd:string")
        prop = SnapshotProperty.from_property(stub)
        assert prop.property_type == "datatype"

    def test_property_type_inferred_object(self) -> None:
        """Properties with range_class should infer property_type='object'."""
        stub = _stub_property(range_datatype=None, range_class="http://example.org/Class")
        prop = SnapshotProperty.from_property(stub)
        assert prop.property_type == "object"


def _fake_property(**overrides):
    """Create a fake Property-like object for testing from_property()."""
    from types import SimpleNamespace

    defaults = {
        "id": uuid4(),
        "identifier": "prop1",
        "uri": "http://example.org/prop1",
        "label": "Test Property",
        "description": None,
        "domain_class": "http://example.org/Class",
        "domain_classes": [],
        "range_scheme_id": None,
        "range_scheme": None,
        "range_class": None,
        "range_datatype": None,
        "cardinality": "single",
        "required": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestFromPropertyTypeInference:
    """from_property() should infer property_type with three-way fallback."""

    def test_datatype_property(self) -> None:
        """Properties with range_datatype infer as 'datatype'."""
        prop = _fake_property(range_datatype="xsd:string")
        snap = SnapshotProperty.from_property(prop)
        assert snap.property_type == "datatype"

    def test_object_property_with_range_class(self) -> None:
        """Properties with range_class (no datatype) infer as 'object'."""
        prop = _fake_property(range_class="http://example.org/Target")
        snap = SnapshotProperty.from_property(prop)
        assert snap.property_type == "object"

    def test_object_property_with_range_scheme(self) -> None:
        """Properties with range_scheme_id (no datatype) infer as 'object'."""
        scheme = _fake_property(uri="http://example.org/scheme")
        prop = _fake_property(range_scheme_id=uuid4(), range_scheme=scheme)
        snap = SnapshotProperty.from_property(prop)
        assert snap.property_type == "object"

    def test_rdf_property_no_range(self) -> None:
        """Properties with no range infer as 'rdf'."""
        prop = _fake_property()
        snap = SnapshotProperty.from_property(prop)
        assert snap.property_type == "rdf"


class TestRequireValidRange:
    """Range validation should be relaxed for rdf property type."""

    def test_rdf_type_allows_zero_ranges(self) -> None:
        """rdf:Property with no range should pass validation."""
        prop = SnapshotProperty(
            id=uuid4(),
            identifier="codedValue",
            uri="http://example.org/codedValue",
            label="Coded Value",
            domain_class_uris=["http://example.org/Class"],
            property_type="rdf",
            range_scheme_id=None,
            range_datatype=None,
            range_class=None,
            cardinality="single",
            required=False,
        )
        assert prop.property_type == "rdf"

    def test_rdf_type_allows_one_range(self) -> None:
        """rdf:Property with one range should pass validation."""
        prop = SnapshotProperty(
            id=uuid4(),
            identifier="codedValue",
            uri="http://example.org/codedValue",
            label="Coded Value",
            domain_class_uris=["http://example.org/Class"],
            property_type="rdf",
            range_datatype="xsd:string",
            cardinality="single",
            required=False,
        )
        assert prop.range_datatype == "xsd:string"

    def test_object_type_requires_exactly_one_range(self) -> None:
        """object property with no range should fail."""
        with pytest.raises(PydanticValidationError):
            SnapshotProperty(
                id=uuid4(),
                identifier="prop1",
                uri="http://example.org/prop1",
                label="Test Prop",
                domain_class_uris=["http://example.org/Class"],
                property_type="object",
                range_scheme_id=None,
                range_datatype=None,
                range_class=None,
                cardinality="single",
                required=False,
            )

    def test_datatype_type_requires_exactly_one_range(self) -> None:
        """datatype property with no range should fail."""
        with pytest.raises(PydanticValidationError):
            SnapshotProperty(
                id=uuid4(),
                identifier="prop1",
                uri="http://example.org/prop1",
                label="Test Prop",
                domain_class_uris=["http://example.org/Class"],
                property_type="datatype",
                range_scheme_id=None,
                range_datatype=None,
                range_class=None,
                cardinality="single",
                required=False,
            )

    def test_object_type_rejects_multiple_ranges(self) -> None:
        """object property with more than one range should fail."""
        with pytest.raises(PydanticValidationError):
            SnapshotProperty(
                id=uuid4(),
                identifier="prop1",
                uri="http://example.org/prop1",
                label="Test Prop",
                domain_class_uris=["http://example.org/Class"],
                property_type="object",
                range_scheme_id=uuid4(),
                range_scheme_uri="http://example.org/scheme",
                range_datatype="xsd:string",
                range_class=None,
                cardinality="single",
                required=False,
            )

    def test_rdf_type_rejects_multiple_ranges(self) -> None:
        """rdf:Property with more than one range should fail."""
        with pytest.raises(PydanticValidationError):
            SnapshotProperty(
                id=uuid4(),
                identifier="codedValue",
                uri="http://example.org/codedValue",
                label="Coded Value",
                domain_class_uris=["http://example.org/Class"],
                property_type="rdf",
                range_datatype="xsd:string",
                range_class="http://example.org/Class",
                cardinality="single",
                required=False,
            )


class TestDomainClassUrisValidation:
    """_validate_references should check domain_class_uris (list) not domain_class (scalar)."""

    def test_all_domain_uris_must_resolve(self) -> None:
        """Each URI in domain_class_uris must exist in project classes."""
        prop = SnapshotProperty.model_construct(
            id=uuid4(),
            identifier="prop1",
            uri="http://example.org/prop1",
            label="Test Property",
            domain_class_uris=["http://example.org/Class", "http://example.org/NonExistent"],
            property_type="object",
            range_datatype="xsd:string",
            cardinality="single",
            required=False,
        )
        cls = _class("Class", uri="http://example.org/Class")
        scheme = _scheme(concepts=[_concept("Term")])
        result = validate_snapshot(_vocab(scheme, properties=[prop], classes=[cls]))
        assert result.valid is False
        errors = [e for e in result.errors if e.code == "broken_domain_class_ref"]
        assert len(errors) == 1

    def test_all_domain_uris_valid(self) -> None:
        """All URIs resolving should pass."""
        cls_a = _class("A", uri="http://example.org/A", identifier="a")
        cls_b = _class("B", uri="http://example.org/B", identifier="b")
        prop = SnapshotProperty.model_construct(
            id=uuid4(),
            identifier="prop1",
            uri="http://example.org/prop1",
            label="Test Property",
            domain_class_uris=["http://example.org/A", "http://example.org/B"],
            property_type="object",
            range_datatype="xsd:string",
            cardinality="single",
            required=False,
        )
        scheme = _scheme(concepts=[_concept("Term")])
        result = validate_snapshot(_vocab(scheme, properties=[prop], classes=[cls_a, cls_b]))
        assert result.valid is True


class TestBrokenDomainClassRef:
    def test_property_domain_class_not_in_classes(self) -> None:
        prop = SnapshotProperty.model_construct(
            id=uuid4(),
            identifier="prop1",
            uri="http://example.org/prop1",
            label="Test Property",
            domain_class_uris=["http://example.org/NonExistent"],
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
            domain_class_uris=["http://example.org/Class"],
            range_datatype="xsd:string",
            cardinality="one",
            required=False,
        )
        concept = _concept("Term")
        scheme = _scheme(concepts=[concept])
        result = validate_snapshot(_vocab(scheme, properties=[prop], classes=[cls]))
        assert result.valid is True
