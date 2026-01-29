"""SKOS Import service for parsing and importing RDF files."""

from uuid import UUID

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.schemas.skos_import import (
    ImportPreviewResponse,
    ImportResultResponse,
    SchemeCreatedResponse,
    SchemePreviewResponse,
)
from taxonomy_builder.services.change_tracker import ChangeTracker


class SKOSImportError(Exception):
    """Base exception for import errors."""


class InvalidRDFError(SKOSImportError):
    """RDF file could not be parsed."""

    def __init__(self, message: str = "Could not parse RDF file") -> None:
        super().__init__(message)


class SchemeURIConflictError(SKOSImportError):
    """Scheme with this URI already exists in project."""

    def __init__(self, uri: str) -> None:
        self.uri = uri
        super().__init__(f"A scheme with URI '{uri}' already exists in this project")


# File extension to RDFLib format mapping
FORMAT_MAP = {
    ".ttl": "turtle",
    ".turtle": "turtle",
    ".rdf": "xml",
    ".xml": "xml",
    ".owl": "xml",
    ".jsonld": "json-ld",
    ".json": "json-ld",
    ".nt": "nt",
    ".n3": "n3",
}


class SKOSImportService:
    """Service for importing SKOS RDF files into concept schemes."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._tracker = ChangeTracker(db)

    def _detect_format(self, filename: str) -> str:
        """Detect RDF format from filename extension."""
        filename_lower = filename.lower()
        for ext, fmt in FORMAT_MAP.items():
            if filename_lower.endswith(ext):
                return fmt
        raise InvalidRDFError(
            f"Unsupported file format. Supported formats: {', '.join(FORMAT_MAP.keys())}"
        )

    def _parse_rdf(self, content: bytes, format: str) -> Graph:
        """Parse RDF content into a graph."""
        g = Graph()
        try:
            g.parse(data=content, format=format)
        except Exception as e:
            raise InvalidRDFError(f"Failed to parse RDF: {e}") from e
        return g

    def _find_all_concepts(self, g: Graph) -> set[URIRef]:
        """Find all concepts including those typed as subclasses of skos:Concept."""
        concepts: set[URIRef] = set()

        # Find direct skos:Concept instances
        for instance in g.subjects(RDF.type, SKOS.Concept):
            if isinstance(instance, URIRef):
                concepts.add(instance)

        # Find instances of subclasses of skos:Concept
        for concept_class in g.transitive_subjects(RDFS.subClassOf, SKOS.Concept):
            for instance in g.subjects(RDF.type, concept_class):
                if isinstance(instance, URIRef):
                    concepts.add(instance)

        return concepts

    def _get_scheme_title(self, g: Graph, scheme_uri: URIRef) -> str:
        """Get scheme title with priority: rdfs:label > skos:prefLabel > dcterms:title > URI."""
        # Try rdfs:label first
        label = g.value(scheme_uri, RDFS.label)
        if label:
            return str(label)

        # Try skos:prefLabel
        label = g.value(scheme_uri, SKOS.prefLabel)
        if label:
            return str(label)

        # Try dcterms:title
        label = g.value(scheme_uri, DCTERMS.title)
        if label:
            return str(label)

        # Fall back to URI local name
        uri_str = str(scheme_uri)
        if "#" in uri_str:
            return uri_str.split("#")[-1]
        return uri_str.rstrip("/").split("/")[-1]

    def _get_scheme_description(self, g: Graph, scheme_uri: URIRef) -> str | None:
        """Get scheme description from rdfs:comment or dcterms:description."""
        desc = g.value(scheme_uri, RDFS.comment)
        if desc:
            return str(desc)
        desc = g.value(scheme_uri, DCTERMS.description)
        if desc:
            return str(desc)
        return None

    def _get_concept_scheme(self, g: Graph, concept_uri: URIRef) -> URIRef | None:
        """Get the scheme a concept belongs to via skos:inScheme or skos:topConceptOf."""
        scheme = g.value(concept_uri, SKOS.inScheme)
        if scheme and isinstance(scheme, URIRef):
            return scheme

        scheme = g.value(concept_uri, SKOS.topConceptOf)
        if scheme and isinstance(scheme, URIRef):
            return scheme

        return None

    def _get_concept_pref_label(self, g: Graph, concept_uri: URIRef) -> tuple[str, str | None]:
        """Get prefLabel for concept, returning (label, warning) tuple."""
        label = g.value(concept_uri, SKOS.prefLabel)
        if label:
            return str(label), None

        # Fall back to URI local name
        uri_str = str(concept_uri)
        if "#" in uri_str:
            local_name = uri_str.split("#")[-1]
        else:
            local_name = uri_str.rstrip("/").split("/")[-1]

        warning = f"Concept {concept_uri} has no prefLabel, using URI fragment: {local_name}"
        return local_name, warning

    def _get_identifier_from_uri(self, uri: URIRef) -> str:
        """Extract identifier (local name) from URI."""
        uri_str = str(uri)
        if "#" in uri_str:
            return uri_str.split("#")[-1]
        return uri_str.rstrip("/").split("/")[-1]

    def _count_broader_relationships(
        self, g: Graph, concepts: set[URIRef]
    ) -> int:
        """Count broader relationships among the given concepts."""
        count = 0
        for concept in concepts:
            for broader in g.objects(concept, SKOS.broader):
                if isinstance(broader, URIRef) and broader in concepts:
                    count += 1
        return count

    async def _check_uri_conflicts(self, project_id: UUID, scheme_uris: list[str]) -> None:
        """Check for URI conflicts with existing schemes."""
        for uri in scheme_uris:
            result = await self.db.execute(
                select(ConceptScheme).where(
                    ConceptScheme.project_id == project_id,
                    ConceptScheme.uri == uri,
                )
            )
            if result.scalar_one_or_none():
                raise SchemeURIConflictError(uri)

    async def _get_unique_title(self, project_id: UUID, base_title: str) -> str:
        """Get a unique title, appending (2), (3), etc. if needed."""
        title = base_title

        # Check if base title exists
        result = await self.db.execute(
            select(ConceptScheme).where(
                ConceptScheme.project_id == project_id,
                ConceptScheme.title == title,
            )
        )
        if not result.scalar_one_or_none():
            return title

        # Find next available number
        counter = 2
        while True:
            title = f"{base_title} ({counter})"
            result = await self.db.execute(
                select(ConceptScheme).where(
                    ConceptScheme.project_id == project_id,
                    ConceptScheme.title == title,
                )
            )
            if not result.scalar_one_or_none():
                return title
            counter += 1

    def _analyze_graph(
        self, g: Graph
    ) -> dict:
        """Analyze the RDF graph and extract scheme/concept structure."""
        # Find all schemes
        schemes: list[URIRef] = []
        for scheme in g.subjects(RDF.type, SKOS.ConceptScheme):
            if isinstance(scheme, URIRef):
                schemes.append(scheme)

        # Find all concepts
        all_concepts = self._find_all_concepts(g)

        # Group concepts by scheme
        concepts_by_scheme: dict[URIRef, set[URIRef]] = {s: set() for s in schemes}
        orphan_concepts: set[URIRef] = set()

        for concept in all_concepts:
            scheme = self._get_concept_scheme(g, concept)
            if scheme and scheme in concepts_by_scheme:
                concepts_by_scheme[scheme].add(concept)
            else:
                orphan_concepts.add(concept)

        # Handle orphan concepts
        warnings: list[str] = []
        if orphan_concepts:
            if len(schemes) == 1:
                # Assign to single scheme
                concepts_by_scheme[schemes[0]].update(orphan_concepts)
            else:
                # Generate warnings for orphans
                for orphan in orphan_concepts:
                    warnings.append(
                        f"Concept {orphan} has no scheme membership and was skipped"
                    )

        return {
            "schemes": schemes,
            "concepts_by_scheme": concepts_by_scheme,
            "warnings": warnings,
        }

    async def preview(
        self, project_id: UUID, content: bytes, filename: str
    ) -> ImportPreviewResponse:
        """Parse RDF and return preview without committing.

        Args:
            project_id: The project to import into
            content: The RDF file content
            filename: The filename (used for format detection)

        Returns:
            ImportPreviewResponse with scheme and concept information

        Raises:
            InvalidRDFError: If the file cannot be parsed
            SchemeURIConflictError: If a scheme URI already exists in the project
        """
        format = self._detect_format(filename)
        g = self._parse_rdf(content, format)

        analysis = self._analyze_graph(g)
        schemes = analysis["schemes"]
        concepts_by_scheme = analysis["concepts_by_scheme"]
        global_warnings = analysis["warnings"]

        # Check for URI conflicts
        scheme_uris = [str(s) for s in schemes]
        await self._check_uri_conflicts(project_id, scheme_uris)

        # Build preview for each scheme
        scheme_previews: list[SchemePreviewResponse] = []
        total_concepts = 0
        total_relationships = 0

        for scheme_uri in schemes:
            concepts = concepts_by_scheme[scheme_uri]
            title = self._get_scheme_title(g, scheme_uri)
            description = self._get_scheme_description(g, scheme_uri)
            relationships = self._count_broader_relationships(g, concepts)

            # Collect warnings for this scheme
            warnings: list[str] = []
            for concept in concepts:
                _, warning = self._get_concept_pref_label(g, concept)
                if warning:
                    warnings.append(warning)

            scheme_previews.append(
                SchemePreviewResponse(
                    title=title,
                    description=description,
                    uri=str(scheme_uri),
                    concepts_count=len(concepts),
                    relationships_count=relationships,
                    warnings=warnings,
                )
            )

            total_concepts += len(concepts)
            total_relationships += relationships

        return ImportPreviewResponse(
            valid=True,
            schemes=scheme_previews,
            total_concepts_count=total_concepts,
            total_relationships_count=total_relationships,
            errors=global_warnings,
        )

    async def execute(
        self, project_id: UUID, content: bytes, filename: str, user_id: UUID | None = None
    ) -> ImportResultResponse:
        """Parse RDF and create schemes/concepts in database.

        Args:
            project_id: The project to import into
            content: The RDF file content
            filename: The filename (used for format detection)
            user_id: The ID of the user performing the import

        Returns:
            ImportResultResponse with created scheme and concept information

        Raises:
            InvalidRDFError: If the file cannot be parsed
            SchemeURIConflictError: If a scheme URI already exists in the project
        """
        format = self._detect_format(filename)
        g = self._parse_rdf(content, format)

        analysis = self._analyze_graph(g)
        schemes = analysis["schemes"]
        concepts_by_scheme = analysis["concepts_by_scheme"]

        # Check for URI conflicts
        scheme_uris = [str(s) for s in schemes]
        await self._check_uri_conflicts(project_id, scheme_uris)

        schemes_created: list[SchemeCreatedResponse] = []
        total_concepts = 0
        total_relationships = 0

        for scheme_uri in schemes:
            concepts = concepts_by_scheme[scheme_uri]

            # Get scheme metadata
            base_title = self._get_scheme_title(g, scheme_uri)
            title = await self._get_unique_title(project_id, base_title)
            description = self._get_scheme_description(g, scheme_uri)

            # Create scheme
            scheme = ConceptScheme(
                project_id=project_id,
                title=title,
                description=description,
                uri=str(scheme_uri),
            )
            self.db.add(scheme)
            await self.db.flush()
            await self.db.refresh(scheme)

            # Record change
            await self._tracker.record(
                scheme_id=scheme.id,
                entity_type="scheme",
                entity_id=scheme.id,
                action="create",
                before=None,
                after=self._tracker.serialize_scheme(scheme),
                user_id=user_id,
            )

            # Create concepts - first pass: create all concepts
            uri_to_concept: dict[URIRef, Concept] = {}

            for concept_uri in concepts:
                pref_label, _ = self._get_concept_pref_label(g, concept_uri)
                identifier = self._get_identifier_from_uri(concept_uri)

                # Get definition
                definition = None
                def_value = g.value(concept_uri, SKOS.definition)
                if def_value:
                    definition = str(def_value)

                # Get scope note
                scope_note = None
                scope_value = g.value(concept_uri, SKOS.scopeNote)
                if scope_value:
                    scope_note = str(scope_value)

                # Get alt labels
                alt_labels: list[str] = []
                for alt in g.objects(concept_uri, SKOS.altLabel):
                    if isinstance(alt, Literal):
                        alt_labels.append(str(alt))

                concept = Concept(
                    scheme_id=scheme.id,
                    pref_label=pref_label,
                    identifier=identifier,
                    definition=definition,
                    scope_note=scope_note,
                    alt_labels=alt_labels,
                )
                self.db.add(concept)
                uri_to_concept[concept_uri] = concept

            await self.db.flush()

            # Refresh all concepts to get IDs
            for concept in uri_to_concept.values():
                await self.db.refresh(concept)

            # Second pass: create broader relationships
            relationship_count = 0
            for concept_uri, concept in uri_to_concept.items():
                for broader_uri in g.objects(concept_uri, SKOS.broader):
                    if isinstance(broader_uri, URIRef) and broader_uri in uri_to_concept:
                        broader_concept = uri_to_concept[broader_uri]
                        rel = ConceptBroader(
                            concept_id=concept.id,
                            broader_concept_id=broader_concept.id,
                        )
                        self.db.add(rel)
                        relationship_count += 1

            await self.db.flush()

            # Record concept changes
            for concept in uri_to_concept.values():
                await self._tracker.record(
                    scheme_id=scheme.id,
                    entity_type="concept",
                    entity_id=concept.id,
                    action="create",
                    before=None,
                    after=self._tracker.serialize_concept(concept),
                    user_id=user_id,
                )

            schemes_created.append(
                SchemeCreatedResponse(
                    id=scheme.id,
                    title=title,
                    concepts_created=len(concepts),
                )
            )

            total_concepts += len(concepts)
            total_relationships += relationship_count

        return ImportResultResponse(
            schemes_created=schemes_created,
            total_concepts_created=total_concepts,
            total_relationships_created=total_relationships,
        )
