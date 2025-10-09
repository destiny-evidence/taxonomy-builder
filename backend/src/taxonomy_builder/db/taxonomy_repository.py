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
