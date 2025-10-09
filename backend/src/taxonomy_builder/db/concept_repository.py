"""Concept repository for data storage."""

from abc import ABC, abstractmethod

from taxonomy_builder.models.concept import Concept


class ConceptRepository(ABC):
    """Abstract base class for concept repositories."""

    @abstractmethod
    def save(self, concept: Concept) -> Concept:
        """Save a concept."""
        pass

    @abstractmethod
    def exists(self, scheme_id: str, concept_id: str) -> bool:
        """Check if a concept with the given ID exists within the scheme."""
        pass

    @abstractmethod
    def get_by_scheme(self, scheme_id: str) -> list[Concept]:
        """Get all concepts for a scheme."""
        pass

    @abstractmethod
    def get_by_id(self, concept_id: str) -> Concept | None:
        """Get a concept by ID. Returns None if not found."""
        pass

    @abstractmethod
    def update(self, concept_id: str, concept: Concept) -> Concept:
        """Update a concept. Assumes concept exists."""
        pass

    @abstractmethod
    def delete(self, concept_id: str) -> None:
        """Delete a concept. Assumes concept exists."""
        pass


class InMemoryConceptRepository(ConceptRepository):
    """In-memory implementation of concept repository."""

    def __init__(self):
        """Initialize the repository with an empty dict."""
        self._concepts: dict[str, Concept] = {}

    def save(self, concept: Concept) -> Concept:
        """Save a concept to the in-memory store."""
        self._concepts[concept.id] = concept
        return concept

    def exists(self, scheme_id: str, concept_id: str) -> bool:
        """Check if a concept exists in the store for the given scheme."""
        concept = self._concepts.get(concept_id)
        return concept is not None and concept.scheme_id == scheme_id

    def get_by_scheme(self, scheme_id: str) -> list[Concept]:
        """Get all concepts for a scheme."""
        return [c for c in self._concepts.values() if c.scheme_id == scheme_id]

    def get_by_id(self, concept_id: str) -> Concept | None:
        """Get a concept by ID. Returns None if not found."""
        return self._concepts.get(concept_id)

    def update(self, concept_id: str, concept: Concept) -> Concept:
        """Update a concept. Assumes concept exists."""
        self._concepts[concept_id] = concept
        return concept

    def delete(self, concept_id: str) -> None:
        """Delete a concept. Assumes concept exists."""
        del self._concepts[concept_id]
