"""Tests for the DiffService."""

from uuid import uuid4

from taxonomy_builder.schemas.snapshot import (
    DiffResult,
    SnapshotClass,
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotProperty,
    SnapshotScheme,
    SnapshotVocabulary,
)
from taxonomy_builder.services.snapshot_service import compute_diff


def _project_meta() -> SnapshotProjectMetadata:
    return SnapshotProjectMetadata.model_construct(id=uuid4(), name="Test")


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


def _scheme(title: str = "S", **kwargs) -> SnapshotScheme:
    defaults = {"uri": "http://example.org/scheme", "concepts": []}
    defaults.update(kwargs)
    return SnapshotScheme.model_construct(
        id=defaults.pop("id", uuid4()), title=title, **defaults
    )


def _concept(label: str, **kwargs) -> SnapshotConcept:
    return SnapshotConcept.model_construct(
        id=kwargs.pop("id", uuid4()), pref_label=label, **kwargs
    )


def _property(label: str, **kwargs) -> SnapshotProperty:
    defaults = {
        "identifier": "prop",
        "domain_class": "SomeClass",
        "cardinality": "1",
        "required": False,
    }
    defaults.update(kwargs)
    return SnapshotProperty.model_construct(
        id=defaults.pop("id", uuid4()), label=label, **defaults
    )


def _class(label: str, uri: str, **kwargs) -> SnapshotClass:
    return SnapshotClass.model_construct(uri=uri, label=label, **kwargs)


class TestNoDiff:
    """When previous and current are identical."""

    def test_empty_snapshots(self) -> None:
        prev = _vocab()
        curr = _vocab()
        result = compute_diff(prev, curr)
        assert isinstance(result, DiffResult)
        assert result.added == []
        assert result.modified == []
        assert result.removed == []

    def test_identical_content(self) -> None:
        scheme_id = uuid4()
        concept_id = uuid4()
        concept = _concept("Term A", id=concept_id, definition="Def")
        scheme = _scheme("Scheme", id=scheme_id, concepts=[concept])
        result = compute_diff(_vocab(scheme), _vocab(scheme))
        assert result.added == []
        assert result.modified == []
        assert result.removed == []


class TestAddedEntities:
    def test_added_scheme(self) -> None:
        prev = _vocab()
        new_scheme = _scheme("New Scheme")
        curr = _vocab(new_scheme)
        result = compute_diff(prev, curr)
        assert len(result.added) == 1
        assert result.added[0].label == "New Scheme"
        assert result.added[0].entity_type == "scheme"

    def test_added_concept(self) -> None:
        scheme_id = uuid4()
        existing = _concept("Old", id=uuid4())
        added = _concept("New", id=uuid4())
        prev = _vocab(_scheme("S", id=scheme_id, concepts=[existing]))
        curr = _vocab(_scheme("S", id=scheme_id, concepts=[existing, added]))
        result = compute_diff(prev, curr)
        assert len(result.added) == 1
        assert result.added[0].label == "New"
        assert result.added[0].entity_type == "concept"

    def test_added_concept_in_new_scheme(self) -> None:
        """A concept in a newly added scheme counts as added."""
        concept = _concept("Fresh")
        new_scheme = _scheme("Brand New", concepts=[concept])
        result = compute_diff(_vocab(), _vocab(new_scheme))
        labels = {item.label for item in result.added}
        assert "Brand New" in labels
        assert "Fresh" in labels


class TestRemovedEntities:
    def test_removed_scheme(self) -> None:
        old_scheme = _scheme("Gone")
        result = compute_diff(_vocab(old_scheme), _vocab())
        assert len(result.removed) == 1
        assert result.removed[0].label == "Gone"
        assert result.removed[0].entity_type == "scheme"

    def test_removed_concept(self) -> None:
        scheme_id = uuid4()
        kept = _concept("Kept", id=uuid4())
        gone = _concept("Gone", id=uuid4())
        prev = _vocab(_scheme("S", id=scheme_id, concepts=[kept, gone]))
        curr = _vocab(_scheme("S", id=scheme_id, concepts=[kept]))
        result = compute_diff(prev, curr)
        assert len(result.removed) == 1
        assert result.removed[0].label == "Gone"

    def test_removed_concept_in_removed_scheme(self) -> None:
        """Concepts in a removed scheme count as removed."""
        concept = _concept("Orphan")
        old_scheme = _scheme("Deleted", concepts=[concept])
        result = compute_diff(_vocab(old_scheme), _vocab())
        labels = {item.label for item in result.removed}
        assert "Deleted" in labels
        assert "Orphan" in labels


class TestModifiedEntities:
    def test_modified_concept_label(self) -> None:
        scheme_id = uuid4()
        cid = uuid4()
        prev = _vocab(_scheme("S", id=scheme_id, concepts=[_concept("Old Label", id=cid)]))
        curr = _vocab(_scheme("S", id=scheme_id, concepts=[_concept("New Label", id=cid)]))
        result = compute_diff(prev, curr)
        assert len(result.modified) == 1
        assert result.modified[0].id == cid
        changes = {c.field: c for c in result.modified[0].changes}
        assert "pref_label" in changes
        assert changes["pref_label"].old == "Old Label"
        assert changes["pref_label"].new == "New Label"

    def test_modified_concept_definition(self) -> None:
        scheme_id = uuid4()
        cid = uuid4()
        prev = _vocab(
            _scheme("S", id=scheme_id, concepts=[_concept("T", id=cid, definition="old")])
        )
        curr = _vocab(
            _scheme("S", id=scheme_id, concepts=[_concept("T", id=cid, definition="new")])
        )
        result = compute_diff(prev, curr)
        assert len(result.modified) == 1
        changes = {c.field: c for c in result.modified[0].changes}
        assert "definition" in changes

    def test_modified_scheme_title(self) -> None:
        sid = uuid4()
        cid = uuid4()
        concept = _concept("C", id=cid)
        prev = _vocab(_scheme("Old Title", id=sid, concepts=[concept]))
        curr = _vocab(_scheme("New Title", id=sid, concepts=[concept]))
        result = compute_diff(prev, curr)
        assert len(result.modified) == 1
        assert result.modified[0].entity_type == "scheme"
        changes = {c.field: c for c in result.modified[0].changes}
        assert "title" in changes

    def test_unchanged_entity_not_in_modified(self) -> None:
        scheme_id = uuid4()
        cid = uuid4()
        concept = _concept("Same", id=cid, definition="same")
        prev = _vocab(_scheme("S", id=scheme_id, concepts=[concept]))
        curr = _vocab(_scheme("S", id=scheme_id, concepts=[concept]))
        result = compute_diff(prev, curr)
        assert result.modified == []


class TestConceptMovedBetweenSchemes:
    def test_moved_concept_shows_as_removed_and_added(self) -> None:
        """A concept moving between schemes appears as removed + added."""
        sid_a, sid_b, cid = uuid4(), uuid4(), uuid4()
        prev = _vocab(
            _scheme("A", id=sid_a, concepts=[_concept("Mover", id=cid)]),
            _scheme("B", id=sid_b),
        )
        curr = _vocab(
            _scheme("A", id=sid_a),
            _scheme("B", id=sid_b, concepts=[_concept("Mover", id=cid)]),
        )
        result = compute_diff(prev, curr)
        assert len(result.removed) == 1
        assert result.removed[0].id == cid
        assert len(result.added) == 1
        assert result.added[0].id == cid
        assert result.modified == []


class TestFirstPublish:
    """When previous is None (first publish), everything is added."""

    def test_first_publish_all_added(self) -> None:
        concept = _concept("First")
        scheme = _scheme("Initial", concepts=[concept])
        result = compute_diff(None, _vocab(scheme))
        assert len(result.added) == 2  # scheme + concept
        assert result.modified == []
        assert result.removed == []

    def test_first_publish_empty_project(self) -> None:
        result = compute_diff(None, _vocab())
        assert result.added == []
        assert result.modified == []
        assert result.removed == []

    def test_first_publish_includes_properties(self) -> None:
        prop = _property("Color")
        result = compute_diff(None, _vocab(properties=[prop]))
        labels = {item.label for item in result.added}
        assert "Color" in labels

    def test_first_publish_includes_classes(self) -> None:
        cls = _class("Document", "http://example.org/Document")
        result = compute_diff(None, _vocab(classes=[cls]))
        labels = {item.label for item in result.added}
        assert "Document" in labels


class TestPropertyDiff:
    def test_added_property(self) -> None:
        prop = _property("Color", id=uuid4())
        prev = _vocab()
        curr = _vocab(properties=[prop])
        result = compute_diff(prev, curr)
        assert len(result.added) == 1
        assert result.added[0].label == "Color"
        assert result.added[0].entity_type == "property"

    def test_removed_property(self) -> None:
        prop = _property("Color", id=uuid4())
        prev = _vocab(properties=[prop])
        curr = _vocab()
        result = compute_diff(prev, curr)
        assert len(result.removed) == 1
        assert result.removed[0].label == "Color"
        assert result.removed[0].entity_type == "property"

    def test_modified_property(self) -> None:
        pid = uuid4()
        prev = _vocab(properties=[_property("Color", id=pid, description="old")])
        curr = _vocab(properties=[_property("Color", id=pid, description="new")])
        result = compute_diff(prev, curr)
        assert len(result.modified) == 1
        assert result.modified[0].entity_type == "property"
        changes = {c.field: c for c in result.modified[0].changes}
        assert "description" in changes

    def test_unchanged_property(self) -> None:
        pid = uuid4()
        prop = _property("Color", id=pid, description="same")
        result = compute_diff(
            _vocab(properties=[prop]), _vocab(properties=[prop])
        )
        assert result.modified == []


class TestClassDiff:
    def test_added_class(self) -> None:
        cls = _class("Document", "http://example.org/Document")
        prev = _vocab()
        curr = _vocab(classes=[cls])
        result = compute_diff(prev, curr)
        assert len(result.added) == 1
        assert result.added[0].label == "Document"
        assert result.added[0].entity_type == "class"
        assert result.added[0].uri == "http://example.org/Document"

    def test_removed_class(self) -> None:
        cls = _class("Document", "http://example.org/Document")
        prev = _vocab(classes=[cls])
        curr = _vocab()
        result = compute_diff(prev, curr)
        assert len(result.removed) == 1
        assert result.removed[0].label == "Document"
        assert result.removed[0].entity_type == "class"

    def test_class_not_in_modified(self) -> None:
        """Classes with same URI are never in modified, even if label changes."""
        prev = _vocab(classes=[_class("Old Name", "http://example.org/Doc")])
        curr = _vocab(classes=[_class("New Name", "http://example.org/Doc")])
        result = compute_diff(prev, curr)
        assert result.modified == []
