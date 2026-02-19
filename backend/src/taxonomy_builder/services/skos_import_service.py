"""SKOS Import service for parsing and importing RDF files."""

from uuid import UUID

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.models.property import Property
from taxonomy_builder.schemas.skos_import import (
    ClassCreatedResponse,
    ClassPreviewResponse,
    ImportPreviewResponse,
    ImportResultResponse,
    PropertyCreatedResponse,
    PropertyPreviewResponse,
    SchemeCreatedResponse,
    SchemePreviewResponse,
)
from taxonomy_builder.services.change_tracker import ChangeTracker

# XSD namespace prefix for abbreviating datatype URIs
XSD_NS = str(XSD)


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
    """Service for importing SKOS RDF files into concept schemes.

    Also handles OWL class and property declarations found in the same file.
    """

    def __init__(self, db: AsyncSession, user_id: UUID | None = None) -> None:
        self.db = db
        self._tracker = ChangeTracker(db, user_id)

    # --- Format detection and parsing ---

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

    # --- URI helpers ---

    def _get_identifier_from_uri(self, uri: URIRef) -> str:
        """Extract identifier (local name) from URI."""
        uri_str = str(uri)
        if "#" in uri_str:
            return uri_str.split("#")[-1]
        return uri_str.rstrip("/").split("/")[-1]

    def _abbreviate_xsd(self, uri_str: str) -> str:
        """Convert full XSD URI to xsd: prefix form, or return as-is."""
        if uri_str.startswith(XSD_NS):
            return "xsd:" + uri_str[len(XSD_NS):]
        return uri_str

    # --- SKOS concept/scheme helpers ---

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

    def _find_concept_subclasses(self, g: Graph) -> set[URIRef]:
        """Find owl:Class URIs that are rdfs:subClassOf skos:Concept."""
        subclasses: set[URIRef] = set()
        for cls in g.transitive_subjects(RDFS.subClassOf, SKOS.Concept):
            if isinstance(cls, URIRef) and cls != SKOS.Concept:
                subclasses.add(cls)
        return subclasses

    def _get_scheme_title(self, g: Graph, scheme_uri: URIRef) -> str:
        """Get scheme title with priority: rdfs:label > skos:prefLabel > dcterms:title > URI."""
        label = g.value(scheme_uri, RDFS.label)
        if label:
            return str(label)

        label = g.value(scheme_uri, SKOS.prefLabel)
        if label:
            return str(label)

        label = g.value(scheme_uri, DCTERMS.title)
        if label:
            return str(label)

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

        uri_str = str(concept_uri)
        if "#" in uri_str:
            local_name = uri_str.split("#")[-1]
        else:
            local_name = uri_str.rstrip("/").split("/")[-1]

        warning = f"Concept {concept_uri} has no prefLabel, using URI fragment: {local_name}"
        return local_name, warning

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

    # --- OWL class helpers ---

    def _find_owl_classes(self, g: Graph) -> list[URIRef]:
        """Find owl:Class instances that are NOT subclasses of skos:Concept and not blank nodes."""
        concept_subclasses = self._find_concept_subclasses(g)

        classes: list[URIRef] = []
        for subject in g.subjects(RDF.type, OWL.Class):
            if not isinstance(subject, URIRef):
                continue
            # Skip union classes
            if (subject, OWL.unionOf, None) in g:
                continue
            # Skip concept subclasses
            if subject in concept_subclasses:
                continue
            classes.append(subject)

        return classes

    def _extract_class_metadata(self, g: Graph, class_uri: URIRef) -> dict:
        """Extract label, description, scope_note for an OWL class."""
        uri_str = str(class_uri)

        label = g.value(class_uri, RDFS.label)
        if not label:
            label = self._get_identifier_from_uri(class_uri)
        else:
            label = str(label)

        description = g.value(class_uri, RDFS.comment)
        scope_note = g.value(class_uri, SKOS.scopeNote)

        return {
            "identifier": self._get_identifier_from_uri(class_uri),
            "label": str(label),
            "description": str(description) if description else None,
            "scope_note": str(scope_note) if scope_note else None,
            "uri": uri_str,
        }

    # --- OWL property helpers ---

    def _find_properties(self, g: Graph) -> list[tuple[URIRef, str]]:
        """Find owl:ObjectProperty and owl:DatatypeProperty instances.

        Returns list of (uri, property_type) tuples.
        """
        properties: list[tuple[URIRef, str]] = []

        for subject in g.subjects(RDF.type, OWL.ObjectProperty):
            if isinstance(subject, URIRef):
                properties.append((subject, "object"))

        for subject in g.subjects(RDF.type, OWL.DatatypeProperty):
            if isinstance(subject, URIRef):
                properties.append((subject, "datatype"))

        return properties

    def _extract_property_metadata(self, g: Graph, prop_uri: URIRef, prop_type: str) -> dict:
        """Extract metadata for a property."""
        label = g.value(prop_uri, RDFS.label)
        if not label:
            label = self._get_identifier_from_uri(prop_uri)
        else:
            label = str(label)

        description = g.value(prop_uri, RDFS.comment)
        domain = g.value(prop_uri, RDFS.domain)
        range_val = g.value(prop_uri, RDFS.range)

        return {
            "identifier": self._get_identifier_from_uri(prop_uri),
            "label": str(label),
            "description": str(description) if description else None,
            "property_type": prop_type,
            "domain_uri": str(domain) if isinstance(domain, URIRef) else None,
            "range_uri": str(range_val) if isinstance(range_val, URIRef) else None,
            "uri": str(prop_uri),
        }

    def _resolve_range_to_scheme(
        self,
        g: Graph,
        range_uri: str,
        scheme_uri_to_id: dict[str, UUID],
    ) -> UUID | None:
        """Resolve a property range URI to a scheme ID using two strategies.

        1. RDF linkage: find concepts typed with the range class, check their inScheme
        2. URI fallback: if range_uri is itself a scheme URI, match directly
        """
        range_ref = URIRef(range_uri)

        # Strategy 1: Follow RDF linkage
        # Find concepts that are instances of the range class
        for instance in g.subjects(RDF.type, range_ref):
            if not isinstance(instance, URIRef):
                continue
            scheme = self._get_concept_scheme(g, instance)
            if scheme and str(scheme) in scheme_uri_to_id:
                return scheme_uri_to_id[str(scheme)]

        # Strategy 2: Direct scheme URI match
        if range_uri in scheme_uri_to_id:
            return scheme_uri_to_id[range_uri]

        return None

    # --- Graph analysis ---

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

        result = await self.db.execute(
            select(ConceptScheme).where(
                ConceptScheme.project_id == project_id,
                ConceptScheme.title == title,
            )
        )
        if not result.scalar_one_or_none():
            return title

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

    def _analyze_graph(self, g: Graph) -> dict:
        """Analyze the RDF graph and extract all entity types."""
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
                concepts_by_scheme[schemes[0]].update(orphan_concepts)
            else:
                for orphan in orphan_concepts:
                    warnings.append(
                        f"Concept {orphan} has no scheme membership and was skipped"
                    )

        # Find OWL classes (standalone, not concept-subclasses)
        owl_classes = self._find_owl_classes(g)
        class_metadata = [self._extract_class_metadata(g, cls) for cls in owl_classes]

        # Find OWL properties
        owl_properties = self._find_properties(g)
        property_metadata = [
            self._extract_property_metadata(g, uri, ptype)
            for uri, ptype in owl_properties
        ]

        return {
            "schemes": schemes,
            "concepts_by_scheme": concepts_by_scheme,
            "warnings": warnings,
            "classes": class_metadata,
            "properties": property_metadata,
        }

    # --- Preview ---

    async def preview(
        self, project_id: UUID, content: bytes, filename: str
    ) -> ImportPreviewResponse:
        """Parse RDF and return preview without committing."""
        format = self._detect_format(filename)
        g = self._parse_rdf(content, format)

        analysis = self._analyze_graph(g)
        schemes = analysis["schemes"]
        concepts_by_scheme = analysis["concepts_by_scheme"]
        global_warnings = analysis["warnings"]
        class_metadata = analysis["classes"]
        property_metadata = analysis["properties"]

        # Check for URI conflicts
        scheme_uris = [str(s) for s in schemes]
        await self._check_uri_conflicts(project_id, scheme_uris)

        # Build scheme URI → title map for range resolution display
        scheme_uri_to_title: dict[str, str] = {}
        for scheme_uri in schemes:
            scheme_uri_to_title[str(scheme_uri)] = self._get_scheme_title(g, scheme_uri)

        # Build preview for each scheme
        scheme_previews: list[SchemePreviewResponse] = []
        total_concepts = 0
        total_relationships = 0

        for scheme_uri in schemes:
            concepts = concepts_by_scheme[scheme_uri]
            title = self._get_scheme_title(g, scheme_uri)
            description = self._get_scheme_description(g, scheme_uri)
            relationships = self._count_broader_relationships(g, concepts)

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

        # Build class previews
        class_previews = [
            ClassPreviewResponse(
                identifier=cm["identifier"],
                label=cm["label"],
                uri=cm["uri"],
            )
            for cm in class_metadata
        ]

        # Build property previews with range scheme resolution
        property_previews: list[PropertyPreviewResponse] = []
        for pm in property_metadata:
            range_scheme_title = None
            if pm["range_uri"] and pm["property_type"] == "object":
                # Try to resolve range to a scheme title for display
                range_ref = URIRef(pm["range_uri"])
                # Check RDF linkage
                for instance in g.subjects(RDF.type, range_ref):
                    if isinstance(instance, URIRef):
                        scheme = self._get_concept_scheme(g, instance)
                        if scheme and str(scheme) in scheme_uri_to_title:
                            range_scheme_title = scheme_uri_to_title[str(scheme)]
                            break
                # Direct scheme match
                if not range_scheme_title and pm["range_uri"] in scheme_uri_to_title:
                    range_scheme_title = scheme_uri_to_title[pm["range_uri"]]

            property_previews.append(
                PropertyPreviewResponse(
                    identifier=pm["identifier"],
                    label=pm["label"],
                    property_type=pm["property_type"],
                    domain_class_uri=pm["domain_uri"],
                    range_uri=pm["range_uri"],
                    range_scheme_title=range_scheme_title,
                )
            )

        return ImportPreviewResponse(
            valid=True,
            schemes=scheme_previews,
            total_concepts_count=total_concepts,
            total_relationships_count=total_relationships,
            classes=class_previews,
            properties=property_previews,
            classes_count=len(class_previews),
            properties_count=len(property_previews),
            errors=global_warnings,
        )

    # --- Execute ---

    async def execute(
        self, project_id: UUID, content: bytes, filename: str
    ) -> ImportResultResponse:
        """Parse RDF and create schemes/concepts/classes/properties in database."""
        format = self._detect_format(filename)
        g = self._parse_rdf(content, format)

        analysis = self._analyze_graph(g)
        schemes = analysis["schemes"]
        concepts_by_scheme = analysis["concepts_by_scheme"]
        class_metadata = analysis["classes"]
        property_metadata = analysis["properties"]

        # Check for URI conflicts
        scheme_uris = [str(s) for s in schemes]
        await self._check_uri_conflicts(project_id, scheme_uris)

        # --- Step 1: Create OntologyClass records ---
        classes_created: list[ClassCreatedResponse] = []
        for cm in class_metadata:
            # Check if class already exists in this project
            existing = await self.db.execute(
                select(OntologyClass).where(
                    OntologyClass.project_id == project_id,
                    OntologyClass.identifier == cm["identifier"],
                )
            )
            if existing.scalar_one_or_none():
                continue  # Skip duplicate

            ont_class = OntologyClass(
                project_id=project_id,
                identifier=cm["identifier"],
                label=cm["label"],
                description=cm["description"],
                scope_note=cm["scope_note"],
            )
            self.db.add(ont_class)
            await self.db.flush()
            await self.db.refresh(ont_class)

            await self._tracker.record(
                project_id=project_id,
                entity_type="ontology_class",
                entity_id=ont_class.id,
                action="create",
                before=None,
                after={
                    "id": str(ont_class.id),
                    "identifier": ont_class.identifier,
                    "label": ont_class.label,
                },
            )

            classes_created.append(
                ClassCreatedResponse(
                    id=ont_class.id,
                    identifier=ont_class.identifier,
                    label=ont_class.label,
                )
            )

        # Build class URI → ID map for range resolution (includes pre-existing classes)
        all_classes = (
            await self.db.execute(
                select(OntologyClass).where(OntologyClass.project_id == project_id)
            )
        ).scalars().all()
        class_uri_to_id: dict[str, UUID] = {
            c.uri: c.id for c in all_classes if c.uri
        }

        # --- Step 2: Create ConceptScheme + Concept records ---
        schemes_created: list[SchemeCreatedResponse] = []
        scheme_uri_to_id: dict[str, UUID] = {}
        total_concepts = 0
        total_relationships = 0

        for scheme_uri in schemes:
            concepts = concepts_by_scheme[scheme_uri]

            base_title = self._get_scheme_title(g, scheme_uri)
            title = await self._get_unique_title(project_id, base_title)
            description = self._get_scheme_description(g, scheme_uri)

            scheme = ConceptScheme(
                project_id=project_id,
                title=title,
                description=description,
                uri=str(scheme_uri),
            )
            self.db.add(scheme)
            await self.db.flush()
            await self.db.refresh(scheme)

            scheme_uri_to_id[str(scheme_uri)] = scheme.id

            await self._tracker.record(
                project_id=project_id,
                entity_type="scheme",
                entity_id=scheme.id,
                action="create",
                before=None,
                after=self._tracker.serialize_scheme(scheme),
                scheme_id=scheme.id,
            )

            # Create concepts - first pass
            uri_to_concept: dict[URIRef, Concept] = {}

            for concept_uri in concepts:
                pref_label, _ = self._get_concept_pref_label(g, concept_uri)
                identifier = self._get_identifier_from_uri(concept_uri)

                definition = None
                def_value = g.value(concept_uri, SKOS.definition)
                if def_value:
                    definition = str(def_value)

                scope_note = None
                scope_value = g.value(concept_uri, SKOS.scopeNote)
                if scope_value:
                    scope_note = str(scope_value)

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

            for concept in uri_to_concept.values():
                await self.db.refresh(concept)

            # Second pass: broader relationships
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

            for concept in uri_to_concept.values():
                await self._tracker.record(
                    project_id=project_id,
                    entity_type="concept",
                    entity_id=concept.id,
                    action="create",
                    before=None,
                    after=self._tracker.serialize_concept(concept),
                    scheme_id=scheme.id,
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

        # --- Step 3: Create Property records ---
        properties_created: list[PropertyCreatedResponse] = []
        warnings: list[str] = []
        for pm in property_metadata:
            identifier = pm["identifier"]
            range_uri = pm["range_uri"]
            prop_type = pm["property_type"]
            domain_uri = pm["domain_uri"] or ""

            range_scheme_id: UUID | None = None
            range_datatype: str | None = None
            range_class_id: UUID | None = None

            if prop_type == "datatype" and range_uri:
                range_datatype = self._abbreviate_xsd(range_uri)
            elif prop_type == "object" and range_uri:
                range_scheme_id = self._resolve_range_to_scheme(
                    g, range_uri, scheme_uri_to_id
                )
                if range_scheme_id is None:
                    # Try to resolve to an OntologyClass in the project
                    range_class_id = class_uri_to_id.get(range_uri)
                    if range_class_id is None:
                        warnings.append(
                            f"Property '{identifier}' range '{range_uri}' "
                            f"not found in project — skipping range"
                        )

            prop = Property(
                project_id=project_id,
                identifier=identifier,
                label=pm["label"],
                description=pm["description"],
                domain_class=domain_uri,
                range_scheme_id=range_scheme_id,
                range_datatype=range_datatype,
                range_class_id=range_class_id,
                cardinality="single",
                required=False,
            )
            self.db.add(prop)
            await self.db.flush()
            await self.db.refresh(prop)

            await self._tracker.record(
                project_id=project_id,
                entity_type="property",
                entity_id=prop.id,
                action="create",
                before=None,
                after={
                    "id": str(prop.id),
                    "identifier": prop.identifier,
                    "label": prop.label,
                    "domain_class": prop.domain_class,
                    "range_scheme_id": str(prop.range_scheme_id) if prop.range_scheme_id else None,
                    "range_datatype": prop.range_datatype,
                },
            )

            properties_created.append(
                PropertyCreatedResponse(
                    id=prop.id,
                    identifier=prop.identifier,
                    label=prop.label,
                    range_scheme_id=prop.range_scheme_id,
                    range_datatype=prop.range_datatype,
                    range_class_id=prop.range_class_id,
                )
            )

        return ImportResultResponse(
            schemes_created=schemes_created,
            total_concepts_created=total_concepts,
            total_relationships_created=total_relationships,
            classes_created=classes_created,
            properties_created=properties_created,
            warnings=warnings,
        )
