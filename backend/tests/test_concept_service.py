"""Unit tests for ConceptService."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from taxonomy_builder.models.concept import Concept, ConceptCreate
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.taxonomy import Taxonomy
from taxonomy_builder.services.concept_service import ConceptService


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    repo = Mock()
    # Configure save to return the concept passed to it
    repo.save.side_effect = lambda c: c
    return repo


@pytest.fixture
def mock_scheme_service():
    """Create a mock concept scheme service for testing."""
    return Mock()


@pytest.fixture
def concept_service(mock_repository, mock_scheme_service):
    """Create a ConceptService with mocked dependencies."""
    return ConceptService(
        repository=mock_repository, scheme_service=mock_scheme_service
    )


# Step 12 Part A: Create Concept


def test_create_concept_returns_concept(
    concept_service, mock_repository, mock_scheme_service
):
    """Test that create_concept returns a Concept object."""
    taxonomy = Taxonomy(
        id="test-taxonomy",
        name="Test Taxonomy",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(UTC),
    )
    scheme = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Test Scheme",
        uri="http://example.org/test/test-scheme",
        created_at=datetime.now(UTC),
    )
    mock_scheme_service.get_scheme.return_value = scheme
    mock_scheme_service.taxonomy_service.get_taxonomy.return_value = taxonomy
    mock_repository.exists.return_value = False

    concept_data = ConceptCreate(
        id="health-outcome",
        pref_label="Health Outcome",
        definition="A health-related result",
    )

    result = concept_service.create_concept("test-scheme", concept_data)

    assert isinstance(result, Concept)
    assert result.id == "health-outcome"
    assert result.scheme_id == "test-scheme"
    assert result.pref_label == "Health Outcome"
    assert result.definition == "A health-related result"
    assert result.broader_ids == []
    assert result.narrower_ids == []


def test_create_concept_requires_valid_scheme(
    concept_service, mock_repository, mock_scheme_service
):
    """Test that create_concept raises ValueError if scheme not found."""
    mock_scheme_service.get_scheme.side_effect = ValueError(
        "ConceptScheme with ID 'nonexistent' not found"
    )

    concept_data = ConceptCreate(id="test", pref_label="Test")

    with pytest.raises(ValueError, match="ConceptScheme with ID 'nonexistent' not found"):
        concept_service.create_concept("nonexistent", concept_data)


def test_create_concept_rejects_duplicate_id(
    concept_service, mock_repository, mock_scheme_service
):
    """Test that create_concept raises ValueError for duplicate ID within scheme."""
    taxonomy = Taxonomy(
        id="test-taxonomy",
        name="Test Taxonomy",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(UTC),
    )
    scheme = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Test Scheme",
        uri="http://example.org/test/test-scheme",
        created_at=datetime.now(UTC),
    )
    mock_scheme_service.get_scheme.return_value = scheme
    mock_scheme_service.taxonomy_service.get_taxonomy.return_value = taxonomy
    mock_repository.exists.return_value = True

    concept_data = ConceptCreate(id="duplicate", pref_label="Duplicate")

    with pytest.raises(
        ValueError,
        match="Concept with ID 'duplicate' already exists in scheme 'test-scheme'",
    ):
        concept_service.create_concept("test-scheme", concept_data)


def test_create_concept_generates_uri(
    concept_service, mock_repository, mock_scheme_service
):
    """Test that create_concept generates URI using scheme's taxonomy uri_prefix + concept id."""
    taxonomy = Taxonomy(
        id="test-taxonomy",
        name="Test Taxonomy",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(UTC),
    )
    scheme = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Test Scheme",
        uri="http://example.org/test/test-scheme",
        created_at=datetime.now(UTC),
    )
    mock_scheme_service.get_scheme.return_value = scheme
    mock_scheme_service.taxonomy_service.get_taxonomy.return_value = taxonomy
    mock_repository.exists.return_value = False

    concept_data = ConceptCreate(id="health-outcome", pref_label="Health Outcome")

    result = concept_service.create_concept("test-scheme", concept_data)

    assert result.uri == "http://example.org/test/health-outcome"


def test_create_concept_validates_pref_label(
    concept_service, mock_repository, mock_scheme_service
):
    """Test that pref_label is required."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ConceptCreate(id="test", pref_label="")


# Step 13 Part A: List Concepts


def test_list_concepts_returns_all_for_scheme(
    concept_service, mock_repository, mock_scheme_service
):
    """Test that list_concepts returns all concepts for a scheme."""
    scheme = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Test Scheme",
        uri="http://example.org/test/test-scheme",
        created_at=datetime.now(UTC),
    )
    mock_scheme_service.get_scheme.return_value = scheme

    concepts = [
        Concept(
            id="concept1",
            scheme_id="test-scheme",
            uri="http://example.org/test/concept1",
            pref_label="Concept 1",
            created_at=datetime.now(UTC),
        ),
        Concept(
            id="concept2",
            scheme_id="test-scheme",
            uri="http://example.org/test/concept2",
            pref_label="Concept 2",
            created_at=datetime.now(UTC),
        ),
    ]
    mock_repository.get_by_scheme.return_value = concepts

    result = concept_service.list_concepts("test-scheme")

    assert result == concepts
    mock_repository.get_by_scheme.assert_called_once_with("test-scheme")


def test_list_concepts_requires_valid_scheme(
    concept_service, mock_repository, mock_scheme_service
):
    """Test that list_concepts raises ValueError if scheme not found."""
    mock_scheme_service.get_scheme.side_effect = ValueError(
        "ConceptScheme with ID 'nonexistent' not found"
    )

    with pytest.raises(ValueError, match="ConceptScheme with ID 'nonexistent' not found"):
        concept_service.list_concepts("nonexistent")


def test_list_concepts_returns_empty_list(
    concept_service, mock_repository, mock_scheme_service
):
    """Test that list_concepts returns empty list when no concepts exist."""
    scheme = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Test Scheme",
        uri="http://example.org/test/test-scheme",
        created_at=datetime.now(UTC),
    )
    mock_scheme_service.get_scheme.return_value = scheme
    mock_repository.get_by_scheme.return_value = []

    result = concept_service.list_concepts("test-scheme")

    assert result == []


# Step 13 Part B: Get Concept by ID


def test_get_concept_returns_concept(concept_service, mock_repository):
    """Test that get_concept returns the requested concept."""
    concept = Concept(
        id="test-concept",
        scheme_id="test-scheme",
        uri="http://example.org/test/test-concept",
        pref_label="Test Concept",
        created_at=datetime.now(UTC),
    )
    mock_repository.get_by_id.return_value = concept

    result = concept_service.get_concept("test-concept")

    assert result == concept
    mock_repository.get_by_id.assert_called_once_with("test-concept")


def test_get_concept_raises_when_not_found(concept_service, mock_repository):
    """Test that get_concept raises ValueError when concept not found."""
    mock_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="Concept with ID 'nonexistent' not found"):
        concept_service.get_concept("nonexistent")


def test_get_concept_includes_relationships(concept_service, mock_repository):
    """Test that get_concept returns broader_ids and narrower_ids."""
    concept = Concept(
        id="test-concept",
        scheme_id="test-scheme",
        uri="http://example.org/test/test-concept",
        pref_label="Test Concept",
        broader_ids=["broader1", "broader2"],
        narrower_ids=["narrower1"],
        created_at=datetime.now(UTC),
    )
    mock_repository.get_by_id.return_value = concept

    result = concept_service.get_concept("test-concept")

    assert result.broader_ids == ["broader1", "broader2"]
    assert result.narrower_ids == ["narrower1"]


# Step 14 Part A: Update Concept


def test_update_concept_returns_updated(concept_service, mock_repository):
    """Test that update_concept returns the updated concept."""
    from taxonomy_builder.models.concept import ConceptUpdate

    existing = Concept(
        id="test-concept",
        scheme_id="test-scheme",
        uri="http://example.org/test/test-concept",
        pref_label="Original Label",
        created_at=datetime.now(UTC),
    )
    updated = Concept(
        id="test-concept",
        scheme_id="test-scheme",
        uri="http://example.org/test/test-concept",
        pref_label="Updated Label",
        created_at=existing.created_at,
    )
    mock_repository.get_by_id.return_value = existing
    mock_repository.update.return_value = updated

    update_data = ConceptUpdate(pref_label="Updated Label")
    result = concept_service.update_concept("test-concept", update_data)

    assert result == updated
    mock_repository.update.assert_called_once()


def test_update_concept_raises_when_not_found(concept_service, mock_repository):
    """Test that update_concept raises ValueError when concept not found."""
    from taxonomy_builder.models.concept import ConceptUpdate

    mock_repository.get_by_id.return_value = None

    update_data = ConceptUpdate(pref_label="New Label")
    with pytest.raises(ValueError, match="Concept with ID 'nonexistent' not found"):
        concept_service.update_concept("nonexistent", update_data)


def test_update_concept_allows_partial_updates(concept_service, mock_repository):
    """Test that update_concept allows updating individual fields."""
    from taxonomy_builder.models.concept import ConceptUpdate

    existing = Concept(
        id="test-concept",
        scheme_id="test-scheme",
        uri="http://example.org/test/test-concept",
        pref_label="Original Label",
        definition="Original definition",
        alt_labels=["alt1"],
        created_at=datetime.now(UTC),
    )
    mock_repository.get_by_id.return_value = existing
    mock_repository.update.side_effect = lambda id, data: data

    # Update only pref_label
    update_data = ConceptUpdate(pref_label="New Label Only")
    result = concept_service.update_concept("test-concept", update_data)

    assert result.pref_label == "New Label Only"
    assert result.definition == "Original definition"
    assert result.alt_labels == ["alt1"]


# Step 14 Part B: Delete Concept


def test_delete_concept_removes_concept(concept_service, mock_repository):
    """Test that delete_concept successfully deletes a concept."""
    mock_repository.get_by_id.return_value = Concept(
        id="test-concept",
        scheme_id="test-scheme",
        uri="http://example.org/test/test-concept",
        pref_label="Test",
        created_at=datetime.now(UTC),
    )
    mock_repository.delete.return_value = None

    concept_service.delete_concept("test-concept")

    mock_repository.delete.assert_called_once_with("test-concept")


def test_delete_concept_raises_when_not_found(concept_service, mock_repository):
    """Test that delete_concept raises ValueError when concept not found."""
    mock_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="Concept with ID 'nonexistent' not found"):
        concept_service.delete_concept("nonexistent")


def test_delete_concept_updates_relationships(concept_service, mock_repository):
    """Test that delete_concept removes concept from broader/narrower of related concepts."""
    concept = Concept(
        id="test-concept",
        scheme_id="test-scheme",
        uri="http://example.org/test/test-concept",
        pref_label="Test",
        broader_ids=["broader1"],
        narrower_ids=["narrower1"],
        created_at=datetime.now(UTC),
    )
    broader = Concept(
        id="broader1",
        scheme_id="test-scheme",
        uri="http://example.org/test/broader1",
        pref_label="Broader",
        narrower_ids=["test-concept"],
        created_at=datetime.now(UTC),
    )
    narrower = Concept(
        id="narrower1",
        scheme_id="test-scheme",
        uri="http://example.org/test/narrower1",
        pref_label="Narrower",
        broader_ids=["test-concept"],
        created_at=datetime.now(UTC),
    )

    def get_by_id_side_effect(cid):
        if cid == "test-concept":
            return concept
        elif cid == "broader1":
            return broader
        elif cid == "narrower1":
            return narrower
        return None

    mock_repository.get_by_id.side_effect = get_by_id_side_effect
    mock_repository.update.side_effect = lambda id, data: data

    concept_service.delete_concept("test-concept")

    # Verify broader concept was updated (narrower_ids should be empty)
    assert mock_repository.update.call_count == 2  # broader and narrower updated
    mock_repository.delete.assert_called_once_with("test-concept")


# Step 15 Part A: Add Broader Relationship


def test_add_broader_creates_bidirectional_link(concept_service, mock_repository):
    """Test that add_broader updates both concepts."""
    concept = Concept(
        id="child",
        scheme_id="test-scheme",
        uri="http://example.org/test/child",
        pref_label="Child",
        broader_ids=[],
        narrower_ids=[],
        created_at=datetime.now(UTC),
    )
    broader = Concept(
        id="parent",
        scheme_id="test-scheme",
        uri="http://example.org/test/parent",
        pref_label="Parent",
        broader_ids=[],
        narrower_ids=[],
        created_at=datetime.now(UTC),
    )

    def get_by_id_side_effect(cid):
        if cid == "child":
            return concept
        elif cid == "parent":
            return broader
        return None

    mock_repository.get_by_id.side_effect = get_by_id_side_effect
    mock_repository.update.side_effect = lambda id, data: data

    result = concept_service.add_broader("child", "parent")

    assert "parent" in result.broader_ids
    # Verify both concepts were updated
    assert mock_repository.update.call_count == 2


def test_add_broader_raises_for_invalid_concepts(concept_service, mock_repository):
    """Test that add_broader raises ValueError if either concept not found."""
    mock_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="Concept with ID 'nonexistent' not found"):
        concept_service.add_broader("nonexistent", "parent")


def test_add_broader_prevents_self_reference(concept_service, mock_repository):
    """Test that add_broader raises ValueError if concept_id == broader_id."""
    concept = Concept(
        id="self",
        scheme_id="test-scheme",
        uri="http://example.org/test/self",
        pref_label="Self",
        created_at=datetime.now(UTC),
    )
    mock_repository.get_by_id.return_value = concept

    with pytest.raises(ValueError, match="cannot be its own broader concept"):
        concept_service.add_broader("self", "self")


def test_add_broader_prevents_cycles(concept_service, mock_repository):
    """Test that add_broader raises ValueError if would create cycle."""
    concept1 = Concept(
        id="concept1",
        scheme_id="test-scheme",
        uri="http://example.org/test/concept1",
        pref_label="Concept 1",
        broader_ids=["concept2"],
        narrower_ids=[],
        created_at=datetime.now(UTC),
    )
    concept2 = Concept(
        id="concept2",
        scheme_id="test-scheme",
        uri="http://example.org/test/concept2",
        pref_label="Concept 2",
        broader_ids=[],
        narrower_ids=["concept1"],
        created_at=datetime.now(UTC),
    )

    def get_by_id_side_effect(cid):
        if cid == "concept1":
            return concept1
        elif cid == "concept2":
            return concept2
        return None

    mock_repository.get_by_id.side_effect = get_by_id_side_effect

    # Try to add concept1 as broader of concept2 (would create cycle)
    with pytest.raises(ValueError, match="cycle"):
        concept_service.add_broader("concept2", "concept1")


# Step 15 Part B: Remove Broader Relationship


def test_remove_broader_removes_bidirectional_link(concept_service, mock_repository):
    """Test that remove_broader updates both concepts."""
    concept = Concept(
        id="child",
        scheme_id="test-scheme",
        uri="http://example.org/test/child",
        pref_label="Child",
        broader_ids=["parent"],
        narrower_ids=[],
        created_at=datetime.now(UTC),
    )
    broader = Concept(
        id="parent",
        scheme_id="test-scheme",
        uri="http://example.org/test/parent",
        pref_label="Parent",
        broader_ids=[],
        narrower_ids=["child"],
        created_at=datetime.now(UTC),
    )

    def get_by_id_side_effect(cid):
        if cid == "child":
            return concept
        elif cid == "parent":
            return broader
        return None

    mock_repository.get_by_id.side_effect = get_by_id_side_effect
    mock_repository.update.side_effect = lambda id, data: data

    result = concept_service.remove_broader("child", "parent")

    assert "parent" not in result.broader_ids
    # Verify both concepts were updated
    assert mock_repository.update.call_count == 2


def test_remove_broader_raises_for_invalid_concepts(concept_service, mock_repository):
    """Test that remove_broader raises ValueError if either concept not found."""
    mock_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="Concept with ID 'nonexistent' not found"):
        concept_service.remove_broader("nonexistent", "parent")


def test_remove_broader_handles_nonexistent_relationship(concept_service, mock_repository):
    """Test that remove_broader handles case where relationship doesn't exist."""
    concept = Concept(
        id="child",
        scheme_id="test-scheme",
        uri="http://example.org/test/child",
        pref_label="Child",
        broader_ids=[],
        narrower_ids=[],
        created_at=datetime.now(UTC),
    )
    broader = Concept(
        id="parent",
        scheme_id="test-scheme",
        uri="http://example.org/test/parent",
        pref_label="Parent",
        broader_ids=[],
        narrower_ids=[],
        created_at=datetime.now(UTC),
    )

    def get_by_id_side_effect(cid):
        if cid == "child":
            return concept
        elif cid == "parent":
            return broader
        return None

    mock_repository.get_by_id.side_effect = get_by_id_side_effect
    mock_repository.update.side_effect = lambda id, data: data

    # Should not raise error even if relationship doesn't exist
    result = concept_service.remove_broader("child", "parent")

    assert result.broader_ids == []
