"""Tests for snapshot validation via Pydantic validators."""

from uuid import UUID, uuid4

from taxonomy_builder.schemas.snapshot import (
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotScheme,
    SnapshotVocabulary,
)
from taxonomy_builder.services.snapshot_service import validate_snapshot


def _project_meta() -> SnapshotProjectMetadata:
    return SnapshotProjectMetadata(id=uuid4(), name="Test")


def _vocab(*schemes: SnapshotScheme) -> SnapshotVocabulary:
    return SnapshotVocabulary.model_construct(
        project=_project_meta(), concept_schemes=list(schemes)
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
) -> SnapshotConcept:
    return SnapshotConcept.model_construct(
        id=id or uuid4(),
        pref_label=pref_label,
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
