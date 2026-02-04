"""Service for parsing core ontology classes and properties from TTL files."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from rdflib import Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS

logger = logging.getLogger(__name__)


@dataclass
class OntologyClass:
    """Represents an OWL class from the ontology."""

    uri: str
    label: str
    comment: str | None = None


@dataclass
class OntologyProperty:
    """Represents an OWL property from the ontology."""

    uri: str
    label: str
    comment: str | None
    domain: list[str]
    range: list[str]
    property_type: Literal["object", "datatype"]


@dataclass
class CoreOntology:
    """The parsed core ontology structure."""

    classes: list[OntologyClass] = field(default_factory=list)
    object_properties: list[OntologyProperty] = field(default_factory=list)
    datatype_properties: list[OntologyProperty] = field(default_factory=list)


class CoreOntologyService:
    """Service for loading and parsing core ontology from TTL content."""

    def parse_from_file(self, file_path: str) -> CoreOntology:
        """Parse a TTL file and extract ontology structure.

        Args:
            file_path: Path to the TTL file.

        Returns:
            CoreOntology with extracted classes and properties.
        """
        content = Path(file_path).read_text()
        return self.parse_from_string(content)

    def parse_from_string(self, ttl_content: str) -> CoreOntology:
        """Parse TTL content and extract ontology structure.

        Args:
            ttl_content: The TTL file content as a string.

        Returns:
            CoreOntology with extracted classes and properties.
        """
        graph = Graph()
        graph.parse(data=ttl_content, format="turtle")

        classes = self._extract_classes(graph)
        object_properties = self._extract_properties(graph, OWL.ObjectProperty, "object")
        datatype_properties = self._extract_properties(
            graph, OWL.DatatypeProperty, "datatype"
        )

        return CoreOntology(
            classes=classes,
            object_properties=object_properties,
            datatype_properties=datatype_properties,
        )

    def _extract_classes(self, graph: Graph) -> list[OntologyClass]:
        """Extract OWL classes from the graph.

        Excludes:
        - Union classes (those with owl:unionOf)
        - Blank nodes
        """
        classes = []

        # Find all subjects that are owl:Class
        for subject in graph.subjects(RDF.type, OWL.Class):
            # Skip blank nodes
            if not isinstance(subject, URIRef):
                continue

            # Skip union classes (those with owl:unionOf)
            if (subject, OWL.unionOf, None) in graph:
                continue

            uri = str(subject)
            label = self._get_label(graph, subject, uri)
            comment = self._get_comment(graph, subject)

            classes.append(
                OntologyClass(
                    uri=uri,
                    label=label,
                    comment=comment,
                )
            )

        return classes

    def _extract_properties(
        self,
        graph: Graph,
        property_type_uri: URIRef,
        property_type: Literal["object", "datatype"],
    ) -> list[OntologyProperty]:
        """Extract OWL properties of a specific type from the graph.

        Args:
            graph: The RDF graph.
            property_type_uri: OWL.ObjectProperty or OWL.DatatypeProperty.
            property_type: "object" or "datatype" for the property_type field.

        Returns:
            List of OntologyProperty objects.
        """
        properties = []

        for subject in graph.subjects(RDF.type, property_type_uri):
            if not isinstance(subject, URIRef):
                continue

            uri = str(subject)
            label = self._get_label(graph, subject, uri)
            comment = self._get_comment(graph, subject)
            domain = self._get_domain_or_range(graph, subject, RDFS.domain)
            range_ = self._get_domain_or_range(graph, subject, RDFS.range)

            properties.append(
                OntologyProperty(
                    uri=uri,
                    label=label,
                    comment=comment,
                    domain=domain,
                    range=range_,
                    property_type=property_type,
                )
            )

        return properties

    def _get_domain_or_range(
        self, graph: Graph, subject: URIRef, predicate: URIRef
    ) -> list[str]:
        """Get domain or range for a property, expanding union classes.

        Args:
            graph: The RDF graph.
            subject: The property URI.
            predicate: RDFS.domain or RDFS.range.

        Returns:
            List of class URIs. If the domain/range is a union class,
            returns the member classes. Otherwise returns a single-item list.
        """
        value = graph.value(subject, predicate)
        if value is None:
            return []

        if not isinstance(value, URIRef):
            return []

        # Check if this is a union class
        union_list = graph.value(value, OWL.unionOf)
        if union_list is not None:
            # Expand the union to its members
            members = []
            collection = Collection(graph, union_list)
            for member in collection:
                if isinstance(member, URIRef):
                    members.append(str(member))
            return members

        return [str(value)]

    def _get_label(self, graph: Graph, subject: URIRef, uri: str) -> str:
        """Get rdfs:label for a subject, falling back to URI fragment."""
        label = graph.value(subject, RDFS.label)
        if label:
            return str(label)

        # Fall back to URI fragment or last path segment
        if "#" in uri:
            return uri.split("#")[-1]
        return uri.rstrip("/").split("/")[-1]

    def _get_comment(self, graph: Graph, subject: URIRef) -> str | None:
        """Get rdfs:comment for a subject."""
        comment = graph.value(subject, RDFS.comment)
        if comment:
            return str(comment)
        return None


# Module-level cache for the core ontology
_core_ontology_cache: CoreOntology | None = None


def load_core_ontology() -> CoreOntology:
    """Load the core ontology from the configured file path.

    This function loads the ontology and caches it. If the file doesn't exist,
    it logs a warning and returns an empty ontology (graceful degradation for dev).

    Returns:
        The parsed CoreOntology, or an empty one if the file is missing.
    """
    global _core_ontology_cache

    from taxonomy_builder.config import settings

    file_path = Path(settings.core_ontology_path)

    if not file_path.exists():
        logger.warning(
            f"Core ontology file not found at {file_path}. "
            "Returning empty ontology. This is expected during development "
            "if the file hasn't been created yet."
        )
        _core_ontology_cache = CoreOntology()
        return _core_ontology_cache

    service = CoreOntologyService()
    _core_ontology_cache = service.parse_from_file(str(file_path))
    return _core_ontology_cache


def get_cached_ontology() -> CoreOntology | None:
    """Get the cached core ontology.

    Returns:
        The cached CoreOntology, or None if not yet loaded.
    """
    return _core_ontology_cache
