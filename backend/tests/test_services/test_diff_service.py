"""Tests for the DiffService."""

from uuid import uuid4

from taxonomy_builder.schemas.snapshot import (
    DiffResult,
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotScheme,
    SnapshotVocabulary,
)
from taxonomy_builder.services.publishing_service import PublishingService


def _project_meta() -> SnapshotProjectMetadata:
    return SnapshotProjectMetadata(id=uuid4(), name="Test")


def _vocab(*schemes: SnapshotScheme) -> SnapshotVocabulary:
    return SnapshotVocabulary(project=_project_meta(), concept_schemes=list(schemes))


def _scheme(title: str = "S", **kwargs) -> SnapshotScheme:
    return SnapshotScheme(id=kwargs.pop("id", uuid4()), title=title, **kwargs)


def _concept(label: str, **kwargs) -> SnapshotConcept:
    return SnapshotConcept(id=kwargs.pop("id", uuid4()), pref_label=label, **kwargs)


class TestNoDiff:
    """When previous and current are identical."""

    def test_empty_snapshots(self) -> None:
        prev = _vocab()
        curr = _vocab()
        result = PublishingService.compute_diff(prev, curr)
        assert isinstance(result, DiffResult)
        assert result.added == []
        assert result.modified == []
        assert result.removed == []

    def test_identical_content(self) -> None:
        scheme_id = uuid4()
        concept_id = uuid4()
        concept = _concept("Term A", id=concept_id, definition="Def")
        scheme = _scheme("Scheme", id=scheme_id, concepts=[concept])
        result = PublishingService.compute_diff(_vocab(scheme), _vocab(scheme))
        assert result.added == []
        assert result.modified == []
        assert result.removed == []


class TestAddedEntities:
    def test_added_scheme(self) -> None:
        prev = _vocab()
        new_scheme = _scheme("New Scheme")
        curr = _vocab(new_scheme)
        result = PublishingService.compute_diff(prev, curr)
        assert len(result.added) == 1
        assert result.added[0].label == "New Scheme"
        assert result.added[0].entity_type == "scheme"

    def test_added_concept(self) -> None:
        scheme_id = uuid4()
        existing = _concept("Old", id=uuid4())
        added = _concept("New", id=uuid4())
        prev = _vocab(_scheme("S", id=scheme_id, concepts=[existing]))
        curr = _vocab(_scheme("S", id=scheme_id, concepts=[existing, added]))
        result = PublishingService.compute_diff(prev, curr)
        assert len(result.added) == 1
        assert result.added[0].label == "New"
        assert result.added[0].entity_type == "concept"

    def test_added_concept_in_new_scheme(self) -> None:
        """A concept in a newly added scheme counts as added."""
        concept = _concept("Fresh")
        new_scheme = _scheme("Brand New", concepts=[concept])
        result = PublishingService.compute_diff(_vocab(), _vocab(new_scheme))
        labels = {item.label for item in result.added}
        assert "Brand New" in labels
        assert "Fresh" in labels


class TestRemovedEntities:
    def test_removed_scheme(self) -> None:
        old_scheme = _scheme("Gone")
        result = PublishingService.compute_diff(_vocab(old_scheme), _vocab())
        assert len(result.removed) == 1
        assert result.removed[0].label == "Gone"
        assert result.removed[0].entity_type == "scheme"

    def test_removed_concept(self) -> None:
        scheme_id = uuid4()
        kept = _concept("Kept", id=uuid4())
        gone = _concept("Gone", id=uuid4())
        prev = _vocab(_scheme("S", id=scheme_id, concepts=[kept, gone]))
        curr = _vocab(_scheme("S", id=scheme_id, concepts=[kept]))
        result = PublishingService.compute_diff(prev, curr)
        assert len(result.removed) == 1
        assert result.removed[0].label == "Gone"

    def test_removed_concept_in_removed_scheme(self) -> None:
        """Concepts in a removed scheme count as removed."""
        concept = _concept("Orphan")
        old_scheme = _scheme("Deleted", concepts=[concept])
        result = PublishingService.compute_diff(_vocab(old_scheme), _vocab())
        labels = {item.label for item in result.removed}
        assert "Deleted" in labels
        assert "Orphan" in labels


class TestModifiedEntities:
    def test_modified_concept_label(self) -> None:
        scheme_id = uuid4()
        cid = uuid4()
        prev = _vocab(_scheme("S", id=scheme_id, concepts=[_concept("Old Label", id=cid)]))
        curr = _vocab(_scheme("S", id=scheme_id, concepts=[_concept("New Label", id=cid)]))
        result = PublishingService.compute_diff(prev, curr)
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
        result = PublishingService.compute_diff(prev, curr)
        assert len(result.modified) == 1
        changes = {c.field: c for c in result.modified[0].changes}
        assert "definition" in changes

    def test_modified_scheme_title(self) -> None:
        sid = uuid4()
        cid = uuid4()
        concept = _concept("C", id=cid)
        prev = _vocab(_scheme("Old Title", id=sid, concepts=[concept]))
        curr = _vocab(_scheme("New Title", id=sid, concepts=[concept]))
        result = PublishingService.compute_diff(prev, curr)
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
        result = PublishingService.compute_diff(prev, curr)
        assert result.modified == []


class TestFirstPublish:
    """When previous is None (first publish), everything is added."""

    def test_first_publish_all_added(self) -> None:
        concept = _concept("First")
        scheme = _scheme("Initial", concepts=[concept])
        result = PublishingService.compute_diff(None, _vocab(scheme))
        assert len(result.added) == 2  # scheme + concept
        assert result.modified == []
        assert result.removed == []

    def test_first_publish_empty_project(self) -> None:
        result = PublishingService.compute_diff(None, _vocab())
        assert result.added == []
        assert result.modified == []
        assert result.removed == []
