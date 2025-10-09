"""Unit tests for TaxonomyService."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from taxonomy_builder.models.taxonomy import Taxonomy, TaxonomyCreate
from taxonomy_builder.services.taxonomy_service import TaxonomyService


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    repo = Mock()
    # Configure save to return the taxonomy passed to it
    repo.save.side_effect = lambda t: t
    return repo


@pytest.fixture
def taxonomy_service(mock_repository):
    """Create a TaxonomyService with mocked repository."""
    return TaxonomyService(repository=mock_repository)


def test_create_taxonomy_returns_taxonomy(taxonomy_service, mock_repository):
    """Test that create_taxonomy returns a Taxonomy object."""
    taxonomy_data = TaxonomyCreate(
        id="climate-health", name="Climate & Health", uri_prefix="http://example.org/climate/"
    )
    mock_repository.exists.return_value = False

    result = taxonomy_service.create_taxonomy(taxonomy_data)

    assert isinstance(result, Taxonomy)
    assert result.id == "climate-health"
    assert result.name == "Climate & Health"
    assert result.uri_prefix == "http://example.org/climate/"


def test_create_taxonomy_with_valid_id(taxonomy_service, mock_repository):
    """Test that user-provided ID is used."""
    taxonomy_data = TaxonomyCreate(
        id="my-taxonomy", name="My Taxonomy", uri_prefix="http://example.org/my/"
    )
    mock_repository.exists.return_value = False

    result = taxonomy_service.create_taxonomy(taxonomy_data)

    assert result.id == "my-taxonomy"


def test_create_taxonomy_validates_uri_prefix(taxonomy_service, mock_repository):
    """Test that URI prefix must be a valid URI."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Invalid URI prefix"):
        TaxonomyCreate(id="test", name="Test", uri_prefix="not-a-valid-uri")


def test_create_taxonomy_stores_in_repository(taxonomy_service, mock_repository):
    """Test that created taxonomy is saved to repository."""
    taxonomy_data = TaxonomyCreate(
        id="test-id", name="Test", uri_prefix="http://example.org/test/"
    )
    mock_repository.exists.return_value = False

    taxonomy_service.create_taxonomy(taxonomy_data)

    mock_repository.save.assert_called_once()
    saved_taxonomy = mock_repository.save.call_args[0][0]
    assert saved_taxonomy.id == "test-id"


def test_create_taxonomy_rejects_duplicate_id(taxonomy_service, mock_repository):
    """Test that duplicate IDs are rejected."""
    taxonomy_data = TaxonomyCreate(
        id="duplicate", name="Duplicate", uri_prefix="http://example.org/dup/"
    )
    mock_repository.exists.return_value = True

    with pytest.raises(ValueError, match="already exists"):
        taxonomy_service.create_taxonomy(taxonomy_data)


def test_create_taxonomy_id_format_validation(taxonomy_service, mock_repository):
    """Test that ID must be a valid slug (lowercase, hyphens, numbers)."""
    from pydantic import ValidationError

    mock_repository.exists.return_value = False

    # Valid slugs
    valid_ids = ["valid-slug", "valid-slug-123", "validslug", "valid123"]
    for valid_id in valid_ids:
        taxonomy_data = TaxonomyCreate(
            id=valid_id, name="Test", uri_prefix="http://example.org/test/"
        )
        result = taxonomy_service.create_taxonomy(taxonomy_data)
        assert result.id == valid_id

    # Invalid slugs
    invalid_ids = [
        ("Invalid-Slug", "Invalid ID format"),
        ("invalid_slug", "Invalid ID format"),
        ("invalid slug", "Invalid ID format"),
        ("Invalid", "Invalid ID format"),
        ("", "ID cannot be empty"),
    ]
    for invalid_id, expected_error in invalid_ids:
        with pytest.raises(ValidationError, match=expected_error):
            TaxonomyCreate(id=invalid_id, name="Test", uri_prefix="http://example.org/test/")


def test_create_taxonomy_sets_created_at(taxonomy_service, mock_repository):
    """Test that created_at timestamp is set."""
    from datetime import UTC

    taxonomy_data = TaxonomyCreate(
        id="test", name="Test", uri_prefix="http://example.org/test/"
    )
    mock_repository.exists.return_value = False

    before = datetime.now(UTC)
    result = taxonomy_service.create_taxonomy(taxonomy_data)
    after = datetime.now(UTC)

    assert result.created_at is not None
    assert before <= result.created_at <= after


def test_create_taxonomy_with_description(taxonomy_service, mock_repository):
    """Test that optional description is stored."""
    taxonomy_data = TaxonomyCreate(
        id="test",
        name="Test",
        uri_prefix="http://example.org/test/",
        description="A test taxonomy",
    )
    mock_repository.exists.return_value = False

    result = taxonomy_service.create_taxonomy(taxonomy_data)

    assert result.description == "A test taxonomy"


def test_list_taxonomies_returns_all(taxonomy_service, mock_repository):
    """Test that list_taxonomies returns all taxonomies from repository."""
    from datetime import UTC

    taxonomies = [
        Taxonomy(
            id="tax1",
            name="Taxonomy 1",
            uri_prefix="http://example.org/tax1/",
            created_at=datetime.now(UTC),
        ),
        Taxonomy(
            id="tax2",
            name="Taxonomy 2",
            uri_prefix="http://example.org/tax2/",
            created_at=datetime.now(UTC),
        ),
    ]
    mock_repository.get_all.return_value = taxonomies

    result = taxonomy_service.list_taxonomies()

    assert result == taxonomies
    mock_repository.get_all.assert_called_once()


def test_list_taxonomies_returns_empty_list(taxonomy_service, mock_repository):
    """Test that list_taxonomies returns empty list when no taxonomies exist."""
    mock_repository.get_all.return_value = []

    result = taxonomy_service.list_taxonomies()

    assert result == []
    mock_repository.get_all.assert_called_once()


def test_get_taxonomy_by_id_returns_taxonomy(taxonomy_service, mock_repository):
    """Test that get_taxonomy returns the requested taxonomy."""
    from datetime import UTC

    taxonomy = Taxonomy(
        id="test-id",
        name="Test Taxonomy",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(UTC),
    )
    mock_repository.get_by_id.return_value = taxonomy

    result = taxonomy_service.get_taxonomy("test-id")

    assert result == taxonomy
    mock_repository.get_by_id.assert_called_once_with("test-id")


def test_get_taxonomy_by_id_raises_when_not_found(taxonomy_service, mock_repository):
    """Test that get_taxonomy raises ValueError when taxonomy not found."""
    mock_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        taxonomy_service.get_taxonomy("nonexistent")


def test_update_taxonomy_returns_updated_taxonomy(taxonomy_service, mock_repository):
    """Test that update_taxonomy returns the updated taxonomy."""
    from datetime import UTC

    from taxonomy_builder.models.taxonomy import TaxonomyUpdate

    existing = Taxonomy(
        id="test-id",
        name="Original Name",
        uri_prefix="http://example.org/original/",
        created_at=datetime.now(UTC),
    )
    updated = Taxonomy(
        id="test-id",
        name="Updated Name",
        uri_prefix="http://example.org/updated/",
        created_at=existing.created_at,
    )
    mock_repository.get_by_id.return_value = existing
    mock_repository.update.return_value = updated

    update_data = TaxonomyUpdate(name="Updated Name", uri_prefix="http://example.org/updated/")
    result = taxonomy_service.update_taxonomy("test-id", update_data)

    assert result == updated
    mock_repository.update.assert_called_once()


def test_update_taxonomy_raises_when_not_found(taxonomy_service, mock_repository):
    """Test that update_taxonomy raises ValueError when taxonomy not found."""
    from taxonomy_builder.models.taxonomy import TaxonomyUpdate

    mock_repository.get_by_id.return_value = None

    update_data = TaxonomyUpdate(name="New Name")
    with pytest.raises(ValueError, match="not found"):
        taxonomy_service.update_taxonomy("nonexistent", update_data)


def test_update_taxonomy_allows_partial_updates(taxonomy_service, mock_repository):
    """Test that update_taxonomy allows updating individual fields."""
    from datetime import UTC

    from taxonomy_builder.models.taxonomy import TaxonomyUpdate

    existing = Taxonomy(
        id="test-id",
        name="Original Name",
        uri_prefix="http://example.org/original/",
        description="Original description",
        created_at=datetime.now(UTC),
    )
    mock_repository.get_by_id.return_value = existing
    # Mock update to return a copy with just the name changed
    mock_repository.update.side_effect = lambda id, data: Taxonomy(
        id=existing.id,
        name=data.name if data.name else existing.name,
        uri_prefix=data.uri_prefix if data.uri_prefix else existing.uri_prefix,
        description=data.description if data.description is not None else existing.description,
        created_at=existing.created_at,
    )

    # Update only name
    update_data = TaxonomyUpdate(name="New Name Only")
    result = taxonomy_service.update_taxonomy("test-id", update_data)

    assert result.name == "New Name Only"
    assert result.uri_prefix == existing.uri_prefix
    assert result.description == existing.description


def test_delete_taxonomy_removes_taxonomy(taxonomy_service, mock_repository):
    """Test that delete_taxonomy successfully deletes a taxonomy."""
    mock_repository.get_by_id.return_value = Taxonomy(
        id="test-id",
        name="Test",
        uri_prefix="http://example.org/test/",
        created_at=datetime.now(),
    )
    mock_repository.delete.return_value = None

    taxonomy_service.delete_taxonomy("test-id")

    mock_repository.delete.assert_called_once_with("test-id")


def test_delete_taxonomy_raises_when_not_found(taxonomy_service, mock_repository):
    """Test that delete_taxonomy raises ValueError when taxonomy not found."""
    mock_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        taxonomy_service.delete_taxonomy("nonexistent")
