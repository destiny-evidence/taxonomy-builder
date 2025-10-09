"""Concept service for business logic."""

from datetime import UTC, datetime

from taxonomy_builder.db.concept_repository import ConceptRepository
from taxonomy_builder.models.concept import Concept, ConceptCreate, ConceptUpdate
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService


class ConceptService:
    """Service for managing concepts."""

    def __init__(
        self, repository: ConceptRepository, scheme_service: ConceptSchemeService
    ):
        """Initialize the service with a repository and concept scheme service."""
        self.repository = repository
        self.scheme_service = scheme_service

    def create_concept(
        self, scheme_id: str, concept_data: ConceptCreate
    ) -> Concept:
        """Create a new concept.

        Args:
            scheme_id: The ID of the scheme this concept belongs to
            concept_data: Data for creating the concept

        Returns:
            The created concept

        Raises:
            ValueError: If scheme doesn't exist or concept ID already exists
        """
        # Validate scheme exists (will raise ValueError if not found)
        scheme = self.scheme_service.get_scheme(scheme_id)

        # Check if concept with this ID already exists in this scheme
        if self.repository.exists(scheme_id, concept_data.id):
            raise ValueError(
                f"Concept with ID '{concept_data.id}' already exists "
                f"in scheme '{scheme_id}'"
            )

        # We need the taxonomy to get the URI prefix
        # In the real implementation, we need to get the taxonomy from scheme
        # For now, we'll need to get the taxonomy through the scheme's taxonomy_service
        taxonomy = self.scheme_service.taxonomy_service.get_taxonomy(scheme.taxonomy_id)

        # Generate URI from taxonomy's uri_prefix + concept id
        uri = f"{taxonomy.uri_prefix}{concept_data.id}"

        # Create the concept
        concept = Concept(
            id=concept_data.id,
            scheme_id=scheme_id,
            uri=uri,
            pref_label=concept_data.pref_label,
            definition=concept_data.definition,
            alt_labels=concept_data.alt_labels or [],
            broader_ids=[],
            narrower_ids=[],
            created_at=datetime.now(UTC),
        )

        # Save to repository
        return self.repository.save(concept)

    def list_concepts(self, scheme_id: str) -> list[Concept]:
        """List all concepts for a scheme.

        Args:
            scheme_id: The ID of the scheme

        Returns:
            List of all concepts for the scheme

        Raises:
            ValueError: If scheme doesn't exist
        """
        # Validate scheme exists (will raise ValueError if not found)
        self.scheme_service.get_scheme(scheme_id)

        return self.repository.get_by_scheme(scheme_id)

    def get_concept(self, concept_id: str) -> Concept:
        """Get a concept by ID.

        Args:
            concept_id: The ID of the concept to retrieve

        Returns:
            The requested concept

        Raises:
            ValueError: If concept with given ID is not found
        """
        concept = self.repository.get_by_id(concept_id)
        if concept is None:
            raise ValueError(f"Concept with ID '{concept_id}' not found")
        return concept

    def update_concept(
        self, concept_id: str, update_data: ConceptUpdate
    ) -> Concept:
        """Update a concept.

        Args:
            concept_id: The ID of the concept to update
            update_data: The fields to update

        Returns:
            The updated concept

        Raises:
            ValueError: If concept with given ID is not found
        """
        existing = self.repository.get_by_id(concept_id)
        if existing is None:
            raise ValueError(f"Concept with ID '{concept_id}' not found")

        # Apply updates - only update fields that are provided
        new_pref_label = (
            update_data.pref_label
            if update_data.pref_label is not None
            else existing.pref_label
        )
        new_definition = (
            update_data.definition
            if update_data.definition is not None
            else existing.definition
        )
        new_alt_labels = (
            update_data.alt_labels
            if update_data.alt_labels is not None
            else existing.alt_labels
        )

        updated = Concept(
            id=existing.id,
            scheme_id=existing.scheme_id,
            uri=existing.uri,
            pref_label=new_pref_label,
            definition=new_definition,
            alt_labels=new_alt_labels,
            broader_ids=existing.broader_ids,
            narrower_ids=existing.narrower_ids,
            created_at=existing.created_at,
        )

        return self.repository.update(concept_id, updated)

    def delete_concept(self, concept_id: str) -> None:
        """Delete a concept.

        Args:
            concept_id: The ID of the concept to delete

        Raises:
            ValueError: If concept with given ID is not found
        """
        existing = self.repository.get_by_id(concept_id)
        if existing is None:
            raise ValueError(f"Concept with ID '{concept_id}' not found")

        # Remove this concept from all related concepts' broader/narrower lists
        for broader_id in existing.broader_ids:
            broader = self.repository.get_by_id(broader_id)
            if broader:
                broader.narrower_ids = [
                    nid for nid in broader.narrower_ids if nid != concept_id
                ]
                self.repository.update(broader_id, broader)

        for narrower_id in existing.narrower_ids:
            narrower = self.repository.get_by_id(narrower_id)
            if narrower:
                narrower.broader_ids = [
                    bid for bid in narrower.broader_ids if bid != concept_id
                ]
                self.repository.update(narrower_id, narrower)

        self.repository.delete(concept_id)

    def add_broader(self, concept_id: str, broader_id: str) -> Concept:
        """Add a broader concept relationship.

        Args:
            concept_id: The ID of the concept
            broader_id: The ID of the broader concept

        Returns:
            The updated concept

        Raises:
            ValueError: If concepts don't exist, self-reference, or would create cycle
        """
        # Validate both concepts exist
        concept = self.get_concept(concept_id)
        broader = self.get_concept(broader_id)

        # Prevent self-reference
        if concept_id == broader_id:
            raise ValueError("A concept cannot be its own broader concept")

        # Check if relationship already exists
        if broader_id in concept.broader_ids:
            return concept  # Already exists, no change needed

        # Check for cycles using depth-first search
        if self._would_create_cycle(concept_id, broader_id):
            raise ValueError(
                "Adding broader relationship would create a cycle"
            )

        # Add bidirectional relationship
        if broader_id not in concept.broader_ids:
            concept.broader_ids.append(broader_id)
        if concept_id not in broader.narrower_ids:
            broader.narrower_ids.append(concept_id)

        # Save both concepts
        self.repository.update(concept_id, concept)
        self.repository.update(broader_id, broader)

        return concept

    def remove_broader(self, concept_id: str, broader_id: str) -> Concept:
        """Remove a broader concept relationship.

        Args:
            concept_id: The ID of the concept
            broader_id: The ID of the broader concept

        Returns:
            The updated concept

        Raises:
            ValueError: If concepts don't exist
        """
        # Validate both concepts exist
        concept = self.get_concept(concept_id)
        broader = self.get_concept(broader_id)

        # Remove bidirectional relationship (no error if doesn't exist)
        if broader_id in concept.broader_ids:
            concept.broader_ids.remove(broader_id)
        if concept_id in broader.narrower_ids:
            broader.narrower_ids.remove(concept_id)

        # Save both concepts
        self.repository.update(concept_id, concept)
        self.repository.update(broader_id, broader)

        return concept

    def _would_create_cycle(self, concept_id: str, broader_id: str) -> bool:
        """Check if adding broader_id as broader of concept_id would create a cycle.

        Uses depth-first search to check if concept_id is reachable from broader_id
        by following broader relationships.

        Args:
            concept_id: The concept that would get a new broader
            broader_id: The proposed broader concept

        Returns:
            True if adding the relationship would create a cycle
        """
        visited = set()

        def dfs(current_id: str) -> bool:
            """Depth-first search to find concept_id starting from current_id."""
            if current_id == concept_id:
                return True
            if current_id in visited:
                return False

            visited.add(current_id)
            current = self.repository.get_by_id(current_id)
            if current is None:
                return False

            # Check all broader concepts recursively
            for bid in current.broader_ids:
                if dfs(bid):
                    return True

            return False

        return dfs(broader_id)
