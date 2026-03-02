"""SKOS Import service for importing parsed RDF into the database."""

from dataclasses import dataclass, field
from uuid import UUID

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import SKOS
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
    ValidationIssueResponse,
)
from taxonomy_builder.services.change_tracker import ChangeTracker
from taxonomy_builder.services.rdf_parser import (
    InvalidRDFError,
    ValidationResult,
    abbreviate_xsd,
    analyze_graph,
    count_broader_relationships,
    detect_format,
    get_concept_pref_label,
    get_identifier_from_uri,
    get_scheme_description,
    get_scheme_title,
    parse_rdf,
    resolve_object_range,
    validate_graph,
)

# Re-export for existing importers (api/projects.py)
__all__ = ["InvalidRDFError", "SKOSImportService"]


class SKOSImportError(Exception):
    """Base exception for import errors."""


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


def _validation_to_responses(
    validation: ValidationResult,
) -> list[ValidationIssueResponse]:
    """Convert ValidationResult issues into API response objects."""
    return [
        ValidationIssueResponse(
            severity=issue.severity,
            type=issue.type,
            message=issue.message,
            entity_uri=issue.entity_uri,
        )
        for issue in validation.errors + validation.warnings + validation.info
    ]


class SKOSImportService:
    """Service for importing SKOS RDF files into concept schemes.

    Also handles OWL class and property declarations found in the same file.
    """

    def __init__(self, db: AsyncSession, user_id: UUID | None = None) -> None:
        self.db = db
        self._tracker = ChangeTracker(db, user_id)

    # --- Preview ---

    async def preview(
        self, project_id: UUID, content: bytes, filename: str
    ) -> ImportPreviewResponse:
        """Parse RDF and return preview without committing."""
        fmt = detect_format(filename)
        g = parse_rdf(content, fmt)

        analysis = analyze_graph(g)

        # Load existing project data for duplicate detection and range resolution
        existing = await self._load_existing_project_data(project_id)

        # Build class_uris for validation (existing + from file)
        file_class_uris = {cm["uri"] for cm in analysis["classes"]}
        all_class_uris = existing.class_uris | file_class_uris

        # Run validation
        validation = validate_graph(g, all_class_uris)
        validation_issues = _validation_to_responses(validation)

        # If validation has errors, return early with valid=false
        if validation.has_errors:
            return ImportPreviewResponse(
                valid=False,
                schemes=[],
                total_concepts_count=0,
                total_relationships_count=0,
                validation_issues=validation_issues,
            )

        # Build combined URI sets (existing + from file)
        scheme_uris = set(existing.scheme_uris)
        scheme_uri_to_title = dict(existing.scheme_uri_to_title)
        for scheme_uri in analysis["schemes"]:
            uri = str(scheme_uri)
            scheme_uris.add(uri)
            scheme_uri_to_title[uri] = get_scheme_title(g, scheme_uri)

        scheme_previews, total_concepts, total_relationships = self._preview_schemes(
            g, analysis["schemes"], analysis["concepts_by_scheme"],
            existing.scheme_uris,
        )
        class_previews = self._preview_classes(
            analysis["classes"], existing.class_uris, existing.class_identifiers
        )
        # Build class_uris from existing + those that will actually be created
        class_uris = existing.class_uris | {cp.uri for cp in class_previews}
        property_previews, prop_warnings = self._preview_properties(
            g, analysis["properties"], existing.property_identifiers,
            existing.property_uris, scheme_uris, scheme_uri_to_title, class_uris,
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
            warnings=analysis["warnings"] + prop_warnings,
            validation_issues=validation_issues,
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
            class_uris={c.uri for c in existing_classes},
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
            title = get_scheme_title(g, scheme_uri)
            description = get_scheme_description(g, scheme_uri)
            relationships = count_broader_relationships(g, concepts)

            warnings: list[str] = []
            for concept in concepts:
                _, warning = get_concept_pref_label(g, concept)
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
        known_ids = set(existing_identifiers)
        known_uris = set(existing_uris)

        for pm in property_metadata:
            if pm["uri"] in known_uris or pm["identifier"] in known_ids:
                continue

            if not pm["domain_uri"]:
                warnings.append(
                    f"Property '{pm['identifier']}' skipped: "
                    f"no rdfs:domain declared"
                )
                continue

            range_scheme_title = None
            if pm["range_uri"] and pm["property_type"] == "object":
                match resolve_object_range(
                    g, pm["range_uri"], scheme_uris, class_uris
                ):
                    case ("scheme", scheme_uri):
                        range_scheme_title = scheme_uri_to_title.get(scheme_uri)
                    case ("ambiguous", _):
                        warnings.append(
                            f"Property '{pm['identifier']}' range '{pm['range_uri']}' "
                            f"matches multiple schemes \u2014 could not resolve"
                        )
                    case None:
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
            known_ids.add(pm["identifier"])
            known_uris.add(pm["uri"])

        return previews, warnings

    # --- Execute ---

    async def execute(
        self, project_id: UUID, content: bytes, filename: str
    ) -> ImportResultResponse:
        """Parse RDF and create schemes/concepts/classes/properties in database."""
        fmt = detect_format(filename)
        g = parse_rdf(content, fmt)

        analysis = analyze_graph(g)

        # Load existing data once for duplicate detection and range resolution
        existing = await self._load_existing_project_data(project_id)

        # Build class_uris for validation (existing + from file)
        file_class_uris = {cm["uri"] for cm in analysis["classes"]}
        all_class_uris = existing.class_uris | file_class_uris

        # Run validation — refuse to import if errors found
        validation = validate_graph(g, all_class_uris)
        if validation.has_errors:
            error_msgs = "; ".join(e.message for e in validation.errors)
            raise SKOSImportError(
                f"Import blocked by validation errors: {error_msgs}"
            )

        validation_issues = _validation_to_responses(validation)

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

        properties_created, prop_warnings = await self._import_properties(
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
            warnings=prop_warnings,
            validation_issues=validation_issues,
        )

    async def _import_classes(
        self, project_id: UUID, class_metadata: list[dict],
        existing_class_uris: set[str], existing_identifiers: set[str],
    ) -> list[ClassCreatedResponse]:
        """Create OntologyClass records, skipping duplicates by URI (identifier fallback)."""
        known_uris = set(existing_class_uris)
        known_identifiers = set(existing_identifiers)

        to_create: list[tuple[OntologyClass, dict]] = []
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
            known_uris.add(cm["uri"])
            known_identifiers.add(cm["identifier"])
            to_create.append((ont_class, cm))

        if not to_create:
            return []

        await self.db.flush()
        for ont_class, _ in to_create:
            await self.db.refresh(ont_class)

        created: list[ClassCreatedResponse] = []
        for ont_class, cm in to_create:
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
            created.append(
                ClassCreatedResponse(
                    id=ont_class.id,
                    identifier=ont_class.identifier,
                    label=ont_class.label,
                    uri=cm["uri"],
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
            base_title = get_scheme_title(g, scheme_uri)
            title = await self._get_unique_title(project_id, base_title)
            description = get_scheme_description(g, scheme_uri)

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
            pref_label, _ = get_concept_pref_label(g, concept_uri)
            identifier = get_identifier_from_uri(concept_uri)

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
        """Create Property records, skipping duplicates, resolving ranges."""
        warnings: list[str] = []
        known_ids = set(existing_prop_ids)
        known_uris = set(existing_prop_uris)
        to_create: list[Property] = []

        for pm in property_metadata:
            identifier = pm["identifier"]
            if pm["uri"] in known_uris or identifier in known_ids:
                continue

            domain_uri = pm["domain_uri"]
            if not domain_uri:
                warnings.append(
                    f"Property '{identifier}' skipped: "
                    f"no rdfs:domain declared"
                )
                continue

            range_uri = pm["range_uri"]
            prop_type = pm["property_type"]

            range_scheme_id: UUID | None = None
            range_datatype: str | None = None
            range_class: str | None = None

            if prop_type == "datatype" and range_uri:
                range_datatype = abbreviate_xsd(range_uri)
            elif prop_type == "object" and range_uri:
                match resolve_object_range(
                    g, range_uri, set(scheme_uri_to_id.keys()), class_uris
                ):
                    case ("scheme", scheme_uri):
                        range_scheme_id = scheme_uri_to_id[scheme_uri]
                    case ("class", uri):
                        range_class = uri
                    case ("ambiguous", _):
                        range_class = range_uri
                        warnings.append(
                            f"Property '{identifier}' range '{range_uri}' "
                            f"matches multiple schemes \u2014 stored as unresolved URI"
                        )
                    case None:
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
                cardinality=pm["cardinality"],
                required=False,
                uri=pm["uri"],
            )
            self.db.add(prop)
            known_ids.add(identifier)
            known_uris.add(pm["uri"])
            to_create.append(prop)

        if to_create:
            await self.db.flush()
            for prop in to_create:
                await self.db.refresh(prop)

        created: list[PropertyCreatedResponse] = []
        for prop in to_create:
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
