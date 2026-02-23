"""SKOS Export service for generating RDF output."""

from uuid import UUID

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.schemas.snapshot import SnapshotClass, SnapshotScheme, SnapshotVocabulary


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
        """Get a scheme with concepts by ID or raise SchemeNotFoundError."""
        result = await self.db.execute(
            select(ConceptScheme)
            .where(ConceptScheme.id == scheme_id)
            .options(
                selectinload(ConceptScheme.concepts).selectinload(Concept.broader),
                selectinload(ConceptScheme.concepts).selectinload(Concept.narrower),
                selectinload(ConceptScheme.concepts).selectinload(Concept._related_as_subject),
                selectinload(ConceptScheme.concepts).selectinload(Concept._related_as_object),
            )
            .execution_options(populate_existing=True)
        )
        scheme = result.scalar_one_or_none()
        if scheme is None:
            raise SchemeNotFoundError(scheme_id)
        return scheme

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

        graph = Graph()

        # Bind namespaces for cleaner output
        graph.bind("skos", SKOS)
        graph.bind("dct", DCTERMS)
        graph.bind("owl", OWL)
        graph.bind("rdfs", RDFS)

        snapshot_scheme = SnapshotScheme.from_scheme(scheme)

        # Ensure scheme uri
        snapshot_scheme.uri = self._get_scheme_uri(scheme)

        # Ensure concept uris
        for concept in snapshot_scheme.concepts:
            if not concept.uri:
                concept.uri = self._get_concept_uri(concept, snapshot_scheme.uri)

        self._add_scheme_to_graph(graph, snapshot_scheme)

        return graph.serialize(format=format)

    async def export_published_version(self, published_version: PublishedVersion, format: str) -> str:
        """Export a published version's snapshot as SKOS RDF.

        Args:
            published_version: The PublishedVersion model containing the snapshot
            format: The RDF format - 'turtle', 'xml', or 'json-ld'

        Returns:
            The serialized RDF as a string
        """
        vocabulary = SnapshotVocabulary.model_validate(published_version.snapshot)

        g = Graph()
        g.bind("skos", SKOS)
        g.bind("dct", DCTERMS)
        g.bind("owl", OWL)
        g.bind("rdfs", RDFS)

        for scheme_snapshot in vocabulary.concept_schemes:
            self._add_scheme_to_graph(g, scheme_snapshot)

        for snapshot_class in vocabulary.classes:
            self._add_class_to_graph(g, snapshot_class)

        return g.serialize(format=format)

    def _add_scheme_to_graph(self, g: Graph, scheme_snapshot: SnapshotScheme) -> None:
        """Add a single concept scheme and its concepts to an RDF graph."""
        scheme_uri = URIRef(scheme_snapshot.uri)

        # Add ConceptScheme
        g.add((scheme_uri, RDF.type, SKOS.ConceptScheme))
        g.add((scheme_uri, DCTERMS.title, Literal(scheme_snapshot.title)))

        if scheme_snapshot.description:
            g.add((scheme_uri, DCTERMS.description, Literal(scheme_snapshot.description)))

        # Build concept URI lookup keyed by ID
        concept_uris: dict[UUID, URIRef] = {}
        for concept in scheme_snapshot.concepts:
            concept_uris[concept.id] = URIRef(concept.uri)

        # Determine which concepts have broader (i.e. are not top concepts)
        has_broader: set[UUID] = {c.id for c in scheme_snapshot.concepts if c.broader_ids}

        # Add Concepts
        for concept in scheme_snapshot.concepts:
            concept_uri = concept_uris[concept.id]

            g.add((concept_uri, RDF.type, SKOS.Concept))
            g.add((concept_uri, SKOS.prefLabel, Literal(concept.pref_label)))
            g.add((concept_uri, SKOS.inScheme, scheme_uri))

            if concept.definition:
                g.add((concept_uri, SKOS.definition, Literal(concept.definition)))
            if concept.scope_note:
                g.add((concept_uri, SKOS.scopeNote, Literal(concept.scope_note)))

            for alt_label in concept.alt_labels:
                g.add((concept_uri, SKOS.altLabel, Literal(alt_label)))

            for broader_id in concept.broader_ids:
                if broader_id in concept_uris:
                    broader_uri = concept_uris[broader_id]
                    g.add((concept_uri, SKOS.broader, broader_uri))
                    g.add((broader_uri, SKOS.narrower, concept_uri))

            for related_id in concept.related_ids:
                if related_id in concept_uris:
                    related_uri = concept_uris[related_id]
                    g.add((concept_uri, SKOS.related, related_uri))

            if concept.id not in has_broader:
                g.add((scheme_uri, SKOS.hasTopConcept, concept_uri))

    def _add_class_to_graph(self, g: Graph, snapshot_class: SnapshotClass) -> None:
        """Add an OWL class to an RDF graph."""
        class_uri = URIRef(snapshot_class.uri)

        g.add((class_uri, RDF.type, OWL.Class))
        g.add((class_uri, RDFS.label, Literal(snapshot_class.label)))

        if snapshot_class.description:
            g.add((class_uri, DCTERMS.description, Literal(snapshot_class.description)))
        if snapshot_class.scope_note:
            g.add((class_uri, SKOS.scopeNote, Literal(snapshot_class.scope_note)))
