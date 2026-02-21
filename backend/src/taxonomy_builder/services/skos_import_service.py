"""SKOS Import service for parsing and importing RDF files."""

from dataclasses import dataclass, field
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


@dataclass
class ExistingProjectData:
    """Pre-loaded project data for duplicate detection and range resolution."""

    scheme_uris: set[str] = field(default_factory=set)
    scheme_uri_to_id: dict[str, UUID] = field(default_factory=dict)
    scheme_uri_to_title: dict[str, str] = field(default_factory=dict)
    class_uris: set[str] = field(default_factory=set)
    class_identifiers: set[str] = field(default_factory=set)
    property_identifiers: set[str] = field(default_factory=set)
    property_uris: set[str] = field(default_factory=set)


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

        Returns list of (uri, property_type) tuples, deduplicated by URI.
        If a property is typed as both ObjectProperty and DatatypeProperty,
        the type is resolved from rdfs:range: XSD range → datatype,
        otherwise → object.
        """
        object_props: set[URIRef] = set()
        datatype_props: set[URIRef] = set()

        for subject in g.subjects(RDF.type, OWL.ObjectProperty):
            if isinstance(subject, URIRef):
                object_props.add(subject)

        for subject in g.subjects(RDF.type, OWL.DatatypeProperty):
            if isinstance(subject, URIRef):
                datatype_props.add(subject)

        all_uris = object_props | datatype_props
        properties: list[tuple[URIRef, str]] = []

        for uri in all_uris:
            is_obj = uri in object_props
            is_dt = uri in datatype_props
            if is_obj and is_dt:
                # Dual-typed: resolve from range
                range_val = g.value(uri, RDFS.range)
                if range_val and str(range_val).startswith(str(XSD)):
                    properties.append((uri, "datatype"))
                else:
                    properties.append((uri, "object"))
            elif is_dt:
                properties.append((uri, "datatype"))
            else:
                properties.append((uri, "object"))

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

    def _resolve_object_range(
        self,
        g: Graph,
        range_uri: str,
        scheme_uris: set[str],
        class_uris: set[str],
    ) -> tuple[str, str] | None:
        """Resolve an object property range URI.

        Returns ("scheme", scheme_uri), ("class", range_uri), or None.

        Strategies:
        1. RDF linkage: find concepts typed with the range class, follow inScheme
        2. Direct scheme URI match
        3. Class URI match
        """
        range_ref = URIRef(range_uri)

        # Strategy 1: Follow RDF linkage to a scheme
        for instance in g.subjects(RDF.type, range_ref):
            if not isinstance(instance, URIRef):
                continue
            scheme = self._get_concept_scheme(g, instance)
            if scheme and str(scheme) in scheme_uris:
                return ("scheme", str(scheme))

        # Strategy 2: Direct scheme URI match
        if range_uri in scheme_uris:
            return ("scheme", range_uri)

        # Strategy 3: Class URI match
        if range_uri in class_uris:
            return ("class", range_uri)

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

        # Load existing project data for duplicate detection and range resolution
        existing = await self._load_existing_project_data(project_id)

        # Build combined URI sets (existing + from file)
        scheme_uris = set(existing.scheme_uris)
        scheme_uri_to_title = dict(existing.scheme_uri_to_title)
        for scheme_uri in analysis["schemes"]:
            uri = str(scheme_uri)
            scheme_uris.add(uri)
            scheme_uri_to_title[uri] = self._get_scheme_title(g, scheme_uri)

        scheme_previews, total_concepts, total_relationships = self._preview_schemes(
            g, analysis["schemes"], analysis["concepts_by_scheme"],
            existing.scheme_uris,
        )
        class_previews = self._preview_classes(
            analysis["classes"], existing.class_uris, existing.class_identifiers
        )
        # Build class_uris from existing + those that will actually be created
        class_uris = existing.class_uris | {cp.uri for cp in class_previews}
        property_previews, warnings = self._preview_properties(
            g, analysis["properties"],
            existing.property_identifiers, existing.property_uris,
            scheme_uris, scheme_uri_to_title, class_uris,
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
            warnings=warnings,
            errors=analysis["warnings"],
        )

    async def _load_existing_project_data(
        self, project_id: UUID
    ) -> ExistingProjectData:
        """Load existing project entities for duplicate detection and range resolution."""
        existing_schemes = (
            await self.db.execute(
                select(ConceptScheme).where(ConceptScheme.project_id == project_id)
            )
        ).scalars().all()

        existing_classes = (
            await self.db.execute(
                select(OntologyClass).where(OntologyClass.project_id == project_id)
            )
        ).scalars().all()

        existing_props = (
            await self.db.execute(
                select(Property).where(Property.project_id == project_id)
            )
        ).scalars().all()

        return ExistingProjectData(
            scheme_uris={s.uri for s in existing_schemes if s.uri},
            scheme_uri_to_id={s.uri: s.id for s in existing_schemes if s.uri},
            scheme_uri_to_title={s.uri: s.title for s in existing_schemes if s.uri},
            class_uris={c.uri for c in existing_classes if c.uri},
            class_identifiers={c.identifier for c in existing_classes},
            property_identifiers={p.identifier for p in existing_props},
            property_uris={p.uri for p in existing_props},
        )

    def _preview_schemes(
        self,
        g: Graph,
        schemes: list[URIRef],
        concepts_by_scheme: dict[URIRef, set[URIRef]],
        existing_scheme_uris: set[str],
    ) -> tuple[list[SchemePreviewResponse], int, int]:
        """Build scheme previews, skipping existing."""
        previews: list[SchemePreviewResponse] = []
        total_concepts = 0
        total_relationships = 0

        for scheme_uri in schemes:
            if str(scheme_uri) in existing_scheme_uris:
                continue

            concepts = concepts_by_scheme[scheme_uri]
            title = self._get_scheme_title(g, scheme_uri)
            description = self._get_scheme_description(g, scheme_uri)
            relationships = self._count_broader_relationships(g, concepts)

            warnings: list[str] = []
            for concept in concepts:
                _, warning = self._get_concept_pref_label(g, concept)
                if warning:
                    warnings.append(warning)

            previews.append(
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

        return previews, total_concepts, total_relationships

    def _preview_classes(
        self,
        class_metadata: list[dict],
        existing_class_uris: set[str],
        existing_identifiers: set[str],
    ) -> list[ClassPreviewResponse]:
        """Build class previews, skipping existing (by URI, with identifier fallback)."""
        return [
            ClassPreviewResponse(
                identifier=cm["identifier"],
                label=cm["label"],
                uri=cm["uri"],
            )
            for cm in class_metadata
            if cm["uri"] not in existing_class_uris
            and cm["identifier"] not in existing_identifiers
        ]

    def _preview_properties(
        self,
        g: Graph,
        property_metadata: list[dict],
        existing_identifiers: set[str],
        existing_uris: set[str],
        scheme_uris: set[str],
        scheme_uri_to_title: dict[str, str],
        class_uris: set[str],
    ) -> tuple[list[PropertyPreviewResponse], list[str]]:
        """Build property previews with range resolution checks, skipping existing."""
        previews: list[PropertyPreviewResponse] = []
        warnings: list[str] = []

        for pm in property_metadata:
            if pm["uri"] in existing_uris or pm["identifier"] in existing_identifiers:
                continue

            range_scheme_title = None
            if pm["range_uri"] and pm["property_type"] == "object":
                resolved = self._resolve_object_range(
                    g, pm["range_uri"], scheme_uris, class_uris
                )
                if resolved and resolved[0] == "scheme":
                    range_scheme_title = scheme_uri_to_title.get(resolved[1])
                elif resolved is None:
                    warnings.append(
                        f"Property '{pm['identifier']}' range '{pm['range_uri']}' "
                        f"not found in project"
                    )

            previews.append(
                PropertyPreviewResponse(
                    identifier=pm["identifier"],
                    label=pm["label"],
                    property_type=pm["property_type"],
                    domain_class_uri=pm["domain_uri"],
                    range_uri=pm["range_uri"],
                    range_scheme_title=range_scheme_title,
                )
            )

        return previews, warnings

    # --- Execute ---

    async def execute(
        self, project_id: UUID, content: bytes, filename: str
    ) -> ImportResultResponse:
        """Parse RDF and create schemes/concepts/classes/properties in database."""
        fmt = self._detect_format(filename)
        g = self._parse_rdf(content, fmt)

        analysis = self._analyze_graph(g)

        # Load existing data once for duplicate detection and range resolution
        existing = await self._load_existing_project_data(project_id)

        classes_created = await self._import_classes(
            project_id, analysis["classes"],
            existing.class_uris, existing.class_identifiers,
        )

        schemes_created, scheme_uri_to_id, total_concepts, total_relationships = (
            await self._import_schemes(
                g, project_id, analysis["schemes"], analysis["concepts_by_scheme"],
                existing.scheme_uri_to_id,
            )
        )

        # Combine existing class URIs with those actually created (not skipped)
        class_uris = existing.class_uris | {c.uri for c in classes_created}

        properties_created, warnings = await self._import_properties(
            g, project_id, analysis["properties"],
            existing.property_identifiers, existing.property_uris,
            scheme_uri_to_id, class_uris,
        )

        return ImportResultResponse(
            schemes_created=schemes_created,
            total_concepts_created=total_concepts,
            total_relationships_created=total_relationships,
            classes_created=classes_created,
            properties_created=properties_created,
            warnings=warnings,
        )

    async def _import_classes(
        self, project_id: UUID, class_metadata: list[dict],
        existing_class_uris: set[str], existing_identifiers: set[str],
    ) -> list[ClassCreatedResponse]:
        """Create OntologyClass records, skipping duplicates by URI (identifier fallback)."""
        known_uris = set(existing_class_uris)
        known_identifiers = set(existing_identifiers)

        created: list[ClassCreatedResponse] = []
        for cm in class_metadata:
            if cm["uri"] in known_uris or cm["identifier"] in known_identifiers:
                continue

            ont_class = OntologyClass(
                project_id=project_id,
                identifier=cm["identifier"],
                label=cm["label"],
                description=cm["description"],
                scope_note=cm["scope_note"],
                uri=cm["uri"],
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

            known_uris.add(cm["uri"])
            known_identifiers.add(cm["identifier"])

            created.append(
                ClassCreatedResponse(
                    id=ont_class.id,
                    identifier=ont_class.identifier,
                    label=ont_class.label,
                    uri=ont_class.uri,
                )
            )
        return created

    async def _import_schemes(
        self,
        g: Graph,
        project_id: UUID,
        schemes: list[URIRef],
        concepts_by_scheme: dict[URIRef, set[URIRef]],
        existing_scheme_uri_to_id: dict[str, UUID],
    ) -> tuple[list[SchemeCreatedResponse], dict[str, UUID], int, int]:
        """Create ConceptScheme and Concept records, skipping existing schemes."""
        scheme_uri_to_id: dict[str, UUID] = dict(existing_scheme_uri_to_id)

        created: list[SchemeCreatedResponse] = []
        total_concepts = 0
        total_relationships = 0

        for scheme_uri in schemes:
            if str(scheme_uri) in scheme_uri_to_id:
                continue

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

            _, relationship_count = await self._import_concepts(
                g, project_id, scheme.id, concepts
            )

            created.append(
                SchemeCreatedResponse(
                    id=scheme.id,
                    title=title,
                    concepts_created=len(concepts),
                )
            )
            total_concepts += len(concepts)
            total_relationships += relationship_count

        return created, scheme_uri_to_id, total_concepts, total_relationships

    async def _import_concepts(
        self,
        g: Graph,
        project_id: UUID,
        scheme_id: UUID,
        concept_uris: set[URIRef],
    ) -> tuple[dict[URIRef, Concept], int]:
        """Create Concept records and broader relationships for a scheme."""
        uri_to_concept: dict[URIRef, Concept] = {}

        for concept_uri in concept_uris:
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
                scheme_id=scheme_id,
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

        # Broader relationships
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
                scheme_id=scheme_id,
            )

        return uri_to_concept, relationship_count

    async def _import_properties(
        self,
        g: Graph,
        project_id: UUID,
        property_metadata: list[dict],
        existing_prop_ids: set[str],
        existing_prop_uris: set[str],
        scheme_uri_to_id: dict[str, UUID],
        class_uris: set[str],
    ) -> tuple[list[PropertyCreatedResponse], list[str]]:
        """Create Property records, skipping duplicates by URI (identifier fallback)."""
        known_uris = set(existing_prop_uris)
        known_identifiers = set(existing_prop_ids)
        created: list[PropertyCreatedResponse] = []
        warnings: list[str] = []

        for pm in property_metadata:
            identifier = pm["identifier"]
            if pm["uri"] in known_uris or identifier in known_identifiers:
                continue

            range_uri = pm["range_uri"]
            prop_type = pm["property_type"]
            domain_uri = pm["domain_uri"]

            range_scheme_id: UUID | None = None
            range_datatype: str | None = None
            range_class: str | None = None

            if prop_type == "datatype" and range_uri:
                range_datatype = self._abbreviate_xsd(range_uri)
            elif prop_type == "object" and range_uri:
                resolved = self._resolve_object_range(
                    g, range_uri, set(scheme_uri_to_id.keys()),
                    class_uris,
                )
                if resolved:
                    kind, uri = resolved
                    if kind == "scheme":
                        range_scheme_id = scheme_uri_to_id[uri]
                    else:
                        range_class = uri
                else:
                    range_class = range_uri
                    warnings.append(
                        f"Property '{identifier}' range '{range_uri}' "
                        f"not found in project \u2014 stored as unresolved URI"
                    )

            prop = Property(
                project_id=project_id,
                identifier=identifier,
                label=pm["label"],
                description=pm["description"],
                domain_class=domain_uri,
                range_scheme_id=range_scheme_id,
                range_datatype=range_datatype,
                range_class=range_class,
                cardinality="single",
                required=False,
                uri=pm["uri"],
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
                    "range_class": prop.range_class,
                },
            )

            known_uris.add(pm["uri"])
            known_identifiers.add(identifier)

            created.append(
                PropertyCreatedResponse(
                    id=prop.id,
                    identifier=prop.identifier,
                    label=prop.label,
                    range_scheme_id=prop.range_scheme_id,
                    range_datatype=prop.range_datatype,
                    range_class=prop.range_class,
                )
            )

        return created, warnings
