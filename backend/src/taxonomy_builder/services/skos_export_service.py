"""SKOS Export service for generating RDF output."""

from uuid import UUID

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, SKOS
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.published_version import PublishedVersion


class SchemeNotFoundError(Exception):
    """Raised when a concept scheme is not found."""

    def __init__(self, scheme_id: UUID) -> None:
        self.scheme_id = scheme_id
        super().__init__(f"Concept scheme with id '{scheme_id}' not found")


# Default base URI for schemes without a URI set
DEFAULT_BASE_URI = "http://example.org/schemes"


class SKOSExportService:
    """Service for exporting concept schemes as SKOS RDF."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_scheme(self, scheme_id: UUID) -> ConceptScheme:
        """Get a scheme by ID or raise SchemeNotFoundError."""
        result = await self.db.execute(select(ConceptScheme).where(ConceptScheme.id == scheme_id))
        scheme = result.scalar_one_or_none()
        if scheme is None:
            raise SchemeNotFoundError(scheme_id)
        return scheme

    async def _get_concepts_for_scheme(self, scheme_id: UUID) -> list[Concept]:
        """Get all concepts for a scheme with broader and related relationships loaded."""
        result = await self.db.execute(
            select(Concept)
            .where(Concept.scheme_id == scheme_id)
            .options(selectinload(Concept.broader))
            .options(selectinload(Concept.scheme))
            .options(selectinload(Concept._related_as_subject))
            .options(selectinload(Concept._related_as_object))
        )
        return list(result.scalars().all())

    def _get_scheme_uri(self, scheme: ConceptScheme) -> URIRef:
        """Get the URI for a scheme, generating a default if not set."""
        if scheme.uri:
            return URIRef(scheme.uri)
        return URIRef(f"{DEFAULT_BASE_URI}/{scheme.id}")

    def _get_concept_uri(self, concept: Concept, scheme_uri: str) -> URIRef:
        """Get the URI for a concept."""
        if concept.identifier:
            return URIRef(f"{scheme_uri.rstrip('/')}/{concept.identifier}")
        return URIRef(f"{scheme_uri.rstrip('/')}/{concept.id}")

    def _build_graph(self, scheme: ConceptScheme, concepts: list[Concept]) -> Graph:
        """Build an RDF graph from a scheme and its concepts."""
        g = Graph()

        # Bind namespaces for cleaner output
        g.bind("skos", SKOS)
        g.bind("dct", DCTERMS)
        g.bind("owl", OWL)

        # Get scheme URI
        scheme_uri = self._get_scheme_uri(scheme)
        scheme_uri_str = str(scheme_uri)

        # Add ConceptScheme
        g.add((scheme_uri, RDF.type, SKOS.ConceptScheme))
        g.add((scheme_uri, DCTERMS.title, Literal(scheme.title)))

        if scheme.description:
            g.add((scheme_uri, DCTERMS.description, Literal(scheme.description)))

        # Track which concepts have broader relationships (are not top concepts)
        has_broader: set[UUID] = set()
        for concept in concepts:
            if concept.broader:
                has_broader.add(concept.id)

        # Add Concepts
        for concept in concepts:
            concept_uri = self._get_concept_uri(concept, scheme_uri_str)

            g.add((concept_uri, RDF.type, SKOS.Concept))
            g.add((concept_uri, SKOS.prefLabel, Literal(concept.pref_label)))
            g.add((concept_uri, SKOS.inScheme, scheme_uri))

            if concept.definition:
                g.add((concept_uri, SKOS.definition, Literal(concept.definition)))
            if concept.scope_note:
                g.add((concept_uri, SKOS.scopeNote, Literal(concept.scope_note)))

            # Add alt labels
            for alt_label in concept.alt_labels:
                g.add((concept_uri, SKOS.altLabel, Literal(alt_label)))

            # Add broader relationships
            for broader_concept in concept.broader:
                broader_uri = self._get_concept_uri(broader_concept, scheme_uri_str)
                g.add((concept_uri, SKOS.broader, broader_uri))
                # Also add inverse narrower relationship
                g.add((broader_uri, SKOS.narrower, concept_uri))

            # Add related relationships (symmetric - add both directions)
            for related_concept in concept.related:
                related_uri = self._get_concept_uri(related_concept, scheme_uri_str)
                g.add((concept_uri, SKOS.related, related_uri))

            # Add hasTopConcept for concepts without broader
            if concept.id not in has_broader:
                g.add((scheme_uri, SKOS.hasTopConcept, concept_uri))

        return g

    async def export_scheme(self, scheme_id: UUID, format: str) -> str:
        """Export a concept scheme as SKOS RDF.

        Args:
            scheme_id: The ID of the scheme to export
            format: The RDF format - 'ttl' (Turtle), 'xml' (RDF/XML), or 'json-ld'

        Returns:
            The serialized RDF as a string

        Raises:
            SchemeNotFoundError: If the scheme doesn't exist
        """
        scheme = await self._get_scheme(scheme_id)
        concepts = await self._get_concepts_for_scheme(scheme_id)

        graph = self._build_graph(scheme, concepts)

        return graph.serialize(format=format)

    async def export_published_version(self, published_version: PublishedVersion, format: str) -> str:
        """Export a published version's snapshot as SKOS RDF.

        Args:
            published_version: The PublishedVersion model containing the snapshot
            format: The RDF format - 'turtle', 'xml', or 'json-ld'

        Returns:
            The serialized RDF as a string
        """
        raise NotImplementedError

    def export_snapshot(self, snapshot: dict, format: str) -> str:
        """Export a version snapshot as SKOS RDF.

        Args:
            snapshot: The snapshot dict containing 'scheme' and 'concepts'
            format: The RDF format - 'ttl' (Turtle), 'xml' (RDF/XML), or 'json-ld'

        Returns:
            The serialized RDF as a string
        """
        graph = self._build_graph_from_snapshot(snapshot)
        return graph.serialize(format=format)

    def _build_graph_from_snapshot(self, snapshot: dict) -> Graph:
        """Build an RDF graph from a snapshot dict."""
        g = Graph()

        # Bind namespaces for cleaner output
        g.bind("skos", SKOS)
        g.bind("dct", DCTERMS)
        g.bind("owl", OWL)

        scheme_data = snapshot["scheme"]
        concepts_data = snapshot["concepts"]

        # Get scheme URI
        scheme_uri_str = scheme_data.get("uri") or f"{DEFAULT_BASE_URI}/{scheme_data['id']}"
        scheme_uri = URIRef(scheme_uri_str)

        # Add ConceptScheme
        g.add((scheme_uri, RDF.type, SKOS.ConceptScheme))
        g.add((scheme_uri, DCTERMS.title, Literal(scheme_data["title"])))

        if scheme_data.get("description"):
            g.add((scheme_uri, DCTERMS.description, Literal(scheme_data["description"])))

        # Build concept ID to URI mapping
        concept_uris: dict[str, URIRef] = {}
        for concept_data in concepts_data:
            concept_id = concept_data["id"]
            if concept_data.get("identifier"):
                concept_uri = URIRef(f"{scheme_uri_str.rstrip('/')}/{concept_data['identifier']}")
            else:
                concept_uri = URIRef(f"{scheme_uri_str.rstrip('/')}/{concept_id}")
            concept_uris[concept_id] = concept_uri

        # Track which concepts have broader relationships (are not top concepts)
        has_broader: set[str] = set()
        for concept_data in concepts_data:
            if concept_data.get("broader_ids"):
                has_broader.add(concept_data["id"])

        # Add Concepts
        for concept_data in concepts_data:
            concept_id = concept_data["id"]
            concept_uri = concept_uris[concept_id]

            g.add((concept_uri, RDF.type, SKOS.Concept))
            g.add((concept_uri, SKOS.prefLabel, Literal(concept_data["pref_label"])))
            g.add((concept_uri, SKOS.inScheme, scheme_uri))

            if concept_data.get("definition"):
                g.add((concept_uri, SKOS.definition, Literal(concept_data["definition"])))
            if concept_data.get("scope_note"):
                g.add((concept_uri, SKOS.scopeNote, Literal(concept_data["scope_note"])))

            # Add alt labels
            for alt_label in concept_data.get("alt_labels", []):
                g.add((concept_uri, SKOS.altLabel, Literal(alt_label)))

            # Add broader relationships
            for broader_id in concept_data.get("broader_ids", []):
                if broader_id in concept_uris:
                    broader_uri = concept_uris[broader_id]
                    g.add((concept_uri, SKOS.broader, broader_uri))
                    g.add((broader_uri, SKOS.narrower, concept_uri))

            # Add related relationships
            for related_id in concept_data.get("related_ids", []):
                if related_id in concept_uris:
                    related_uri = concept_uris[related_id]
                    g.add((concept_uri, SKOS.related, related_uri))

            # Add hasTopConcept for concepts without broader
            if concept_id not in has_broader:
                g.add((scheme_uri, SKOS.hasTopConcept, concept_uri))

        return g
