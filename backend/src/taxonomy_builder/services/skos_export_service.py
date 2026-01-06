"""SKOS Export service for generating RDF output."""

from uuid import UUID

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, SKOS
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme


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
        result = await self.db.execute(
            select(ConceptScheme).where(ConceptScheme.id == scheme_id)
        )
        scheme = result.scalar_one_or_none()
        if scheme is None:
            raise SchemeNotFoundError(scheme_id)
        return scheme

    async def _get_concepts_for_scheme(self, scheme_id: UUID) -> list[Concept]:
        """Get all concepts for a scheme with broader relationships loaded."""
        result = await self.db.execute(
            select(Concept)
            .where(Concept.scheme_id == scheme_id)
            .options(selectinload(Concept.broader))
            .options(selectinload(Concept.scheme))
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
        if scheme.publisher:
            g.add((scheme_uri, DCTERMS.publisher, Literal(scheme.publisher)))
        if scheme.version:
            g.add((scheme_uri, OWL.versionInfo, Literal(scheme.version)))

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

            # Add broader relationships
            for broader_concept in concept.broader:
                broader_uri = self._get_concept_uri(broader_concept, scheme_uri_str)
                g.add((concept_uri, SKOS.broader, broader_uri))
                # Also add inverse narrower relationship
                g.add((broader_uri, SKOS.narrower, concept_uri))

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
