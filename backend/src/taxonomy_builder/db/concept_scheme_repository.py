"""ConceptScheme repository for data storage."""

from abc import ABC, abstractmethod

from taxonomy_builder.models.concept_scheme import ConceptScheme


class ConceptSchemeRepository(ABC):
    """Abstract base class for concept scheme repositories."""

    @abstractmethod
    def save(self, scheme: ConceptScheme) -> ConceptScheme:
        """Save a concept scheme."""
        pass

    @abstractmethod
    def exists(self, taxonomy_id: str, scheme_id: str) -> bool:
        """Check if a concept scheme with the given ID exists within the taxonomy."""
        pass

    @abstractmethod
    def get_by_taxonomy(self, taxonomy_id: str) -> list[ConceptScheme]:
        """Get all concept schemes for a taxonomy."""
        pass

    @abstractmethod
    def get_by_id(self, scheme_id: str) -> ConceptScheme | None:
        """Get a concept scheme by ID. Returns None if not found."""
        pass

    @abstractmethod
    def update(self, scheme_id: str, scheme: ConceptScheme) -> ConceptScheme:
        """Update a concept scheme. Assumes scheme exists."""
        pass

    @abstractmethod
    def delete(self, scheme_id: str) -> None:
        """Delete a concept scheme. Assumes scheme exists."""
        pass


class InMemoryConceptSchemeRepository(ConceptSchemeRepository):
    """In-memory implementation of concept scheme repository."""

    def __init__(self):
        """Initialize the repository with an empty dict."""
        self._schemes: dict[str, ConceptScheme] = {}

    def save(self, scheme: ConceptScheme) -> ConceptScheme:
        """Save a concept scheme to the in-memory store."""
        self._schemes[scheme.id] = scheme
        return scheme

    def exists(self, taxonomy_id: str, scheme_id: str) -> bool:
        """Check if a concept scheme exists in the store for the given taxonomy."""
        scheme = self._schemes.get(scheme_id)
        return scheme is not None and scheme.taxonomy_id == taxonomy_id

    def get_by_taxonomy(self, taxonomy_id: str) -> list[ConceptScheme]:
        """Get all concept schemes for a taxonomy."""
        return [s for s in self._schemes.values() if s.taxonomy_id == taxonomy_id]

    def get_by_id(self, scheme_id: str) -> ConceptScheme | None:
        """Get a concept scheme by ID. Returns None if not found."""
        return self._schemes.get(scheme_id)

    def update(self, scheme_id: str, scheme: ConceptScheme) -> ConceptScheme:
        """Update a concept scheme. Assumes scheme exists."""
        self._schemes[scheme_id] = scheme
        return scheme

    def delete(self, scheme_id: str) -> None:
        """Delete a concept scheme. Assumes scheme exists."""
        del self._schemes[scheme_id]
