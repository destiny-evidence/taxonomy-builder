"""Taxonomy repository for data storage."""

from abc import ABC, abstractmethod

from taxonomy_builder.models.taxonomy import Taxonomy


class TaxonomyRepository(ABC):
    """Abstract base class for taxonomy repositories."""

    @abstractmethod
    def save(self, taxonomy: Taxonomy) -> Taxonomy:
        """Save a taxonomy."""
        pass

    @abstractmethod
    def exists(self, taxonomy_id: str) -> bool:
        """Check if a taxonomy with the given ID exists."""
        pass

    @abstractmethod
    def get_all(self) -> list[Taxonomy]:
        """Get all taxonomies."""
        pass

    @abstractmethod
    def get_by_id(self, taxonomy_id: str) -> Taxonomy | None:
        """Get a taxonomy by ID. Returns None if not found."""
        pass

    @abstractmethod
    def update(self, taxonomy_id: str, taxonomy: Taxonomy) -> Taxonomy:
        """Update a taxonomy. Assumes taxonomy exists."""
        pass

    @abstractmethod
    def delete(self, taxonomy_id: str) -> None:
        """Delete a taxonomy. Assumes taxonomy exists."""
        pass


class InMemoryTaxonomyRepository(TaxonomyRepository):
    """In-memory implementation of taxonomy repository."""

    def __init__(self):
        """Initialize the repository with an empty dict."""
        self._taxonomies: dict[str, Taxonomy] = {}

    def save(self, taxonomy: Taxonomy) -> Taxonomy:
        """Save a taxonomy to the in-memory store."""
        self._taxonomies[taxonomy.id] = taxonomy
        return taxonomy

    def exists(self, taxonomy_id: str) -> bool:
        """Check if a taxonomy exists in the store."""
        return taxonomy_id in self._taxonomies

    def get_all(self) -> list[Taxonomy]:
        """Get all taxonomies from the store."""
        return list(self._taxonomies.values())

    def get_by_id(self, taxonomy_id: str) -> Taxonomy | None:
        """Get a taxonomy by ID. Returns None if not found."""
        return self._taxonomies.get(taxonomy_id)

    def update(self, taxonomy_id: str, taxonomy: Taxonomy) -> Taxonomy:
        """Update a taxonomy. Assumes taxonomy exists."""
        self._taxonomies[taxonomy_id] = taxonomy
        return taxonomy

    def delete(self, taxonomy_id: str) -> None:
        """Delete a taxonomy. Assumes taxonomy exists."""
        del self._taxonomies[taxonomy_id]
