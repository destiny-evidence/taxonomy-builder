"""Taxonomy service for business logic."""

from datetime import UTC, datetime

from taxonomy_builder.db.taxonomy_repository import TaxonomyRepository
from taxonomy_builder.models.taxonomy import Taxonomy, TaxonomyCreate


class TaxonomyService:
    """Service for managing taxonomies."""

    def __init__(self, repository: TaxonomyRepository):
        """Initialize the service with a repository."""
        self.repository = repository

    def create_taxonomy(self, taxonomy_data: TaxonomyCreate) -> Taxonomy:
        """Create a new taxonomy.

        Args:
            taxonomy_data: Data for creating the taxonomy

        Returns:
            The created taxonomy

        Raises:
            ValueError: If taxonomy ID already exists or validation fails
        """
        # Check if taxonomy with this ID already exists
        if self.repository.exists(taxonomy_data.id):
            raise ValueError(f"Taxonomy with ID '{taxonomy_data.id}' already exists")

        # Create the taxonomy
        taxonomy = Taxonomy(
            id=taxonomy_data.id,
            name=taxonomy_data.name,
            uri_prefix=taxonomy_data.uri_prefix,
            description=taxonomy_data.description,
            created_at=datetime.now(UTC),
        )

        # Save to repository
        return self.repository.save(taxonomy)

    def list_taxonomies(self) -> list[Taxonomy]:
        """List all taxonomies.

        Returns:
            List of all taxonomies
        """
        return self.repository.get_all()

    def get_taxonomy(self, taxonomy_id: str) -> Taxonomy:
        """Get a taxonomy by ID.

        Args:
            taxonomy_id: The ID of the taxonomy to retrieve

        Returns:
            The requested taxonomy

        Raises:
            ValueError: If taxonomy with given ID is not found
        """
        taxonomy = self.repository.get_by_id(taxonomy_id)
        if taxonomy is None:
            raise ValueError(f"Taxonomy with ID '{taxonomy_id}' not found")
        return taxonomy
