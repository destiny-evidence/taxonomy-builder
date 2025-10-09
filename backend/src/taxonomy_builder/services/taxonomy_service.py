"""Taxonomy service for business logic."""

from datetime import UTC, datetime

from taxonomy_builder.db.taxonomy_repository import TaxonomyRepository
from taxonomy_builder.models.taxonomy import Taxonomy, TaxonomyCreate, TaxonomyUpdate


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

    def update_taxonomy(self, taxonomy_id: str, update_data: TaxonomyUpdate) -> Taxonomy:
        """Update a taxonomy.

        Args:
            taxonomy_id: The ID of the taxonomy to update
            update_data: The fields to update

        Returns:
            The updated taxonomy

        Raises:
            ValueError: If taxonomy with given ID is not found
        """
        existing = self.repository.get_by_id(taxonomy_id)
        if existing is None:
            raise ValueError(f"Taxonomy with ID '{taxonomy_id}' not found")

        # Apply updates - only update fields that are provided
        new_name = update_data.name if update_data.name is not None else existing.name
        new_uri_prefix = (
            update_data.uri_prefix if update_data.uri_prefix is not None else existing.uri_prefix
        )
        new_description = (
            update_data.description if update_data.description is not None else existing.description
        )

        updated = Taxonomy(
            id=existing.id,
            name=new_name,
            uri_prefix=new_uri_prefix,
            description=new_description,
            created_at=existing.created_at,
        )

        return self.repository.update(taxonomy_id, updated)
