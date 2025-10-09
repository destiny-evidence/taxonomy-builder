"""Unit tests for ConceptSchemeService."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from taxonomy_builder.models.concept_scheme import ConceptScheme, ConceptSchemeCreate
from taxonomy_builder.models.taxonomy import Taxonomy
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    repo = Mock()
    # Configure save to return the scheme passed to it
    repo.save.side_effect = lambda s: s
    return repo


@pytest.fixture
def mock_taxonomy_service():
    """Create a mock taxonomy service for testing."""
    return Mock()


@pytest.fixture
def concept_scheme_service(mock_repository, mock_taxonomy_service):
    """Create a ConceptSchemeService with mocked dependencies."""
    return ConceptSchemeService(
        repository=mock_repository, taxonomy_service=mock_taxonomy_service
    )


def test_create_scheme_returns_scheme(
    concept_scheme_service, mock_repository, mock_taxonomy_service
):
    """Test that create_scheme returns a ConceptScheme object."""
    from datetime import UTC

    taxonomy = Taxonomy(
        id="test-taxonomy",
        name="Test Taxonomy",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(UTC),
    )
    mock_taxonomy_service.get_taxonomy.return_value = taxonomy
    mock_repository.exists.return_value = False

    scheme_data = ConceptSchemeCreate(
        id="intervention", name="Intervention", description="Test scheme"
    )

    result = concept_scheme_service.create_scheme("test-taxonomy", scheme_data)

    assert isinstance(result, ConceptScheme)
    assert result.id == "intervention"
    assert result.taxonomy_id == "test-taxonomy"
    assert result.name == "Intervention"
    assert result.description == "Test scheme"


def test_create_scheme_requires_valid_taxonomy(
    concept_scheme_service, mock_repository, mock_taxonomy_service
):
    """Test that create_scheme raises ValueError if taxonomy not found."""
    mock_taxonomy_service.get_taxonomy.side_effect = ValueError(
        "Taxonomy with ID 'nonexistent' not found"
    )

    scheme_data = ConceptSchemeCreate(id="test", name="Test")

    with pytest.raises(ValueError, match="Taxonomy with ID 'nonexistent' not found"):
        concept_scheme_service.create_scheme("nonexistent", scheme_data)


def test_create_scheme_rejects_duplicate_id(
    concept_scheme_service, mock_repository, mock_taxonomy_service
):
    """Test that create_scheme raises ValueError for duplicate ID within taxonomy."""
    from datetime import UTC

    taxonomy = Taxonomy(
        id="test-taxonomy",
        name="Test Taxonomy",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(UTC),
    )
    mock_taxonomy_service.get_taxonomy.return_value = taxonomy
    mock_repository.exists.return_value = True

    scheme_data = ConceptSchemeCreate(id="duplicate", name="Duplicate")

    with pytest.raises(
        ValueError,
        match="ConceptScheme with ID 'duplicate' already exists in taxonomy 'test-taxonomy'",
    ):
        concept_scheme_service.create_scheme("test-taxonomy", scheme_data)


def test_create_scheme_generates_uri(
    concept_scheme_service, mock_repository, mock_taxonomy_service
):
    """Test that create_scheme generates URI using taxonomy's uri_prefix + scheme id."""
    from datetime import UTC

    taxonomy = Taxonomy(
        id="test-taxonomy",
        name="Test Taxonomy",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(UTC),
    )
    mock_taxonomy_service.get_taxonomy.return_value = taxonomy
    mock_repository.exists.return_value = False

    scheme_data = ConceptSchemeCreate(id="intervention", name="Intervention")

    result = concept_scheme_service.create_scheme("test-taxonomy", scheme_data)

    assert result.uri == "http://example.org/test/intervention"


# Step 10 Part A: List ConceptSchemes


def test_list_schemes_returns_all_for_taxonomy(
    concept_scheme_service, mock_repository, mock_taxonomy_service
):
    """Test that list_schemes returns all schemes for a taxonomy."""
    from datetime import UTC

    taxonomy = Taxonomy(
        id="test-taxonomy",
        name="Test Taxonomy",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(UTC),
    )
    mock_taxonomy_service.get_taxonomy.return_value = taxonomy

    schemes = [
        ConceptScheme(
            id="scheme1",
            taxonomy_id="test-taxonomy",
            name="Scheme 1",
            uri="http://example.org/test/scheme1",
            created_at=datetime.now(UTC),
        ),
        ConceptScheme(
            id="scheme2",
            taxonomy_id="test-taxonomy",
            name="Scheme 2",
            uri="http://example.org/test/scheme2",
            created_at=datetime.now(UTC),
        ),
    ]
    mock_repository.get_by_taxonomy.return_value = schemes

    result = concept_scheme_service.list_schemes("test-taxonomy")

    assert result == schemes
    mock_repository.get_by_taxonomy.assert_called_once_with("test-taxonomy")


def test_list_schemes_requires_valid_taxonomy(
    concept_scheme_service, mock_repository, mock_taxonomy_service
):
    """Test that list_schemes raises ValueError if taxonomy not found."""
    mock_taxonomy_service.get_taxonomy.side_effect = ValueError(
        "Taxonomy with ID 'nonexistent' not found"
    )

    with pytest.raises(ValueError, match="Taxonomy with ID 'nonexistent' not found"):
        concept_scheme_service.list_schemes("nonexistent")


def test_list_schemes_returns_empty_list(
    concept_scheme_service, mock_repository, mock_taxonomy_service
):
    """Test that list_schemes returns empty list when no schemes exist."""
    from datetime import UTC

    taxonomy = Taxonomy(
        id="test-taxonomy",
        name="Test Taxonomy",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(UTC),
    )
    mock_taxonomy_service.get_taxonomy.return_value = taxonomy
    mock_repository.get_by_taxonomy.return_value = []

    result = concept_scheme_service.list_schemes("test-taxonomy")

    assert result == []


# Step 10 Part B: Get ConceptScheme by ID


def test_get_scheme_returns_scheme(concept_scheme_service, mock_repository):
    """Test that get_scheme returns the requested scheme."""
    from datetime import UTC

    scheme = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Test Scheme",
        uri="http://example.org/test/test-scheme",
        created_at=datetime.now(UTC),
    )
    mock_repository.get_by_id.return_value = scheme

    result = concept_scheme_service.get_scheme("test-scheme")

    assert result == scheme
    mock_repository.get_by_id.assert_called_once_with("test-scheme")


def test_get_scheme_raises_when_not_found(concept_scheme_service, mock_repository):
    """Test that get_scheme raises ValueError when scheme not found."""
    mock_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="ConceptScheme with ID 'nonexistent' not found"):
        concept_scheme_service.get_scheme("nonexistent")


# Step 11 Part A: Update ConceptScheme


def test_update_scheme_returns_updated(concept_scheme_service, mock_repository):
    """Test that update_scheme returns the updated scheme."""
    from datetime import UTC

    from taxonomy_builder.models.concept_scheme import ConceptSchemeUpdate

    existing = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Original Name",
        uri="http://example.org/test/test-scheme",
        created_at=datetime.now(UTC),
    )
    updated = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Updated Name",
        uri="http://example.org/test/test-scheme",
        created_at=existing.created_at,
    )
    mock_repository.get_by_id.return_value = existing
    mock_repository.update.return_value = updated

    update_data = ConceptSchemeUpdate(name="Updated Name")
    result = concept_scheme_service.update_scheme("test-scheme", update_data)

    assert result == updated
    mock_repository.update.assert_called_once()


def test_update_scheme_raises_when_not_found(concept_scheme_service, mock_repository):
    """Test that update_scheme raises ValueError when scheme not found."""
    from taxonomy_builder.models.concept_scheme import ConceptSchemeUpdate

    mock_repository.get_by_id.return_value = None

    update_data = ConceptSchemeUpdate(name="New Name")
    with pytest.raises(ValueError, match="ConceptScheme with ID 'nonexistent' not found"):
        concept_scheme_service.update_scheme("nonexistent", update_data)


def test_update_scheme_allows_partial_updates(concept_scheme_service, mock_repository):
    """Test that update_scheme allows updating individual fields."""
    from datetime import UTC

    from taxonomy_builder.models.concept_scheme import ConceptSchemeUpdate

    existing = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Original Name",
        uri="http://example.org/test/test-scheme",
        description="Original description",
        created_at=datetime.now(UTC),
    )
    mock_repository.get_by_id.return_value = existing
    mock_repository.update.side_effect = lambda id, data: data

    # Update only name
    update_data = ConceptSchemeUpdate(name="New Name Only")
    result = concept_scheme_service.update_scheme("test-scheme", update_data)

    assert result.name == "New Name Only"
    assert result.description == "Original description"


# Step 11 Part B: Delete ConceptScheme


def test_delete_scheme_removes_scheme(concept_scheme_service, mock_repository):
    """Test that delete_scheme successfully deletes a scheme."""
    from datetime import UTC

    mock_repository.get_by_id.return_value = ConceptScheme(
        id="test-scheme",
        taxonomy_id="test-taxonomy",
        name="Test",
        uri="http://example.org/test/test-scheme",
        created_at=datetime.now(UTC),
    )
    mock_repository.delete.return_value = None

    concept_scheme_service.delete_scheme("test-scheme")

    mock_repository.delete.assert_called_once_with("test-scheme")


def test_delete_scheme_raises_when_not_found(concept_scheme_service, mock_repository):
    """Test that delete_scheme raises ValueError when scheme not found."""
    mock_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="ConceptScheme with ID 'nonexistent' not found"):
        concept_scheme_service.delete_scheme("nonexistent")
