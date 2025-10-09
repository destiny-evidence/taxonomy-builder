"""ConceptScheme service for business logic."""

from datetime import UTC, datetime

from taxonomy_builder.db.concept_scheme_repository import ConceptSchemeRepository
from taxonomy_builder.models.concept_scheme import (
    ConceptScheme,
    ConceptSchemeCreate,
    ConceptSchemeUpdate,
)
from taxonomy_builder.services.taxonomy_service import TaxonomyService


class ConceptSchemeService:
    """Service for managing concept schemes."""

    def __init__(
        self, repository: ConceptSchemeRepository, taxonomy_service: TaxonomyService
    ):
        """Initialize the service with a repository and taxonomy service."""
        self.repository = repository
        self.taxonomy_service = taxonomy_service

    def create_scheme(
        self, taxonomy_id: str, scheme_data: ConceptSchemeCreate
    ) -> ConceptScheme:
        """Create a new concept scheme.

        Args:
            taxonomy_id: The ID of the taxonomy this scheme belongs to
            scheme_data: Data for creating the concept scheme

        Returns:
            The created concept scheme

        Raises:
            ValueError: If taxonomy doesn't exist or scheme ID already exists
        """
        # Validate taxonomy exists (will raise ValueError if not found)
        taxonomy = self.taxonomy_service.get_taxonomy(taxonomy_id)

        # Check if scheme with this ID already exists in this taxonomy
        if self.repository.exists(taxonomy_id, scheme_data.id):
            raise ValueError(
                f"ConceptScheme with ID '{scheme_data.id}' already exists "
                f"in taxonomy '{taxonomy_id}'"
            )

        # Generate URI from taxonomy's uri_prefix + scheme id
        uri = f"{taxonomy.uri_prefix}{scheme_data.id}"

        # Create the concept scheme
        scheme = ConceptScheme(
            id=scheme_data.id,
            taxonomy_id=taxonomy_id,
            name=scheme_data.name,
            uri=uri,
            description=scheme_data.description,
            created_at=datetime.now(UTC),
        )

        # Save to repository
        return self.repository.save(scheme)

    def list_schemes(self, taxonomy_id: str) -> list[ConceptScheme]:
        """List all concept schemes for a taxonomy.

        Args:
            taxonomy_id: The ID of the taxonomy

        Returns:
            List of all concept schemes for the taxonomy

        Raises:
            ValueError: If taxonomy doesn't exist
        """
        # Validate taxonomy exists (will raise ValueError if not found)
        self.taxonomy_service.get_taxonomy(taxonomy_id)

        return self.repository.get_by_taxonomy(taxonomy_id)

    def get_scheme(self, scheme_id: str) -> ConceptScheme:
        """Get a concept scheme by ID.

        Args:
            scheme_id: The ID of the concept scheme to retrieve

        Returns:
            The requested concept scheme

        Raises:
            ValueError: If concept scheme with given ID is not found
        """
        scheme = self.repository.get_by_id(scheme_id)
        if scheme is None:
            raise ValueError(f"ConceptScheme with ID '{scheme_id}' not found")
        return scheme

    def update_scheme(
        self, scheme_id: str, update_data: ConceptSchemeUpdate
    ) -> ConceptScheme:
        """Update a concept scheme.

        Args:
            scheme_id: The ID of the concept scheme to update
            update_data: The fields to update

        Returns:
            The updated concept scheme

        Raises:
            ValueError: If concept scheme with given ID is not found
        """
        existing = self.repository.get_by_id(scheme_id)
        if existing is None:
            raise ValueError(f"ConceptScheme with ID '{scheme_id}' not found")

        # Apply updates - only update fields that are provided
        new_name = update_data.name if update_data.name is not None else existing.name
        new_description = (
            update_data.description
            if update_data.description is not None
            else existing.description
        )

        updated = ConceptScheme(
            id=existing.id,
            taxonomy_id=existing.taxonomy_id,
            name=new_name,
            uri=existing.uri,
            description=new_description,
            created_at=existing.created_at,
        )

        return self.repository.update(scheme_id, updated)

    def delete_scheme(self, scheme_id: str) -> None:
        """Delete a concept scheme.

        Args:
            scheme_id: The ID of the concept scheme to delete

        Raises:
            ValueError: If concept scheme with given ID is not found
        """
        existing = self.repository.get_by_id(scheme_id)
        if existing is None:
            raise ValueError(f"ConceptScheme with ID '{scheme_id}' not found")

        self.repository.delete(scheme_id)
