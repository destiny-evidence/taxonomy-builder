"""Service for parsing core ontology classes and properties from TTL files."""

from dataclasses import dataclass, field

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS


@dataclass
class OntologyClass:
    """Represents an OWL class from the ontology."""

    uri: str
    label: str
    comment: str | None = None


@dataclass
class CoreOntology:
    """The parsed core ontology structure."""

    classes: list[OntologyClass] = field(default_factory=list)


class CoreOntologyService:
    """Service for loading and parsing core ontology from TTL content."""

    def parse_from_string(self, ttl_content: str) -> CoreOntology:
        """Parse TTL content and extract ontology structure.

        Args:
            ttl_content: The TTL file content as a string.

        Returns:
            CoreOntology with extracted classes.
        """
        graph = Graph()
        graph.parse(data=ttl_content, format="turtle")

        classes = self._extract_classes(graph)

        return CoreOntology(classes=classes)

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
