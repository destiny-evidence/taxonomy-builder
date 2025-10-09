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
