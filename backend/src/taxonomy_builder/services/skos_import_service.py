"""SKOS Import service for importing parsed RDF into the database."""

from dataclasses import dataclass, field
from uuid import UUID

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import SKOS
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.class_restriction import ClassRestriction
from taxonomy_builder.models.class_superclass import ClassSuperclass
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_broader import ConceptBroader
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.models.property import Property
from taxonomy_builder.models.property_domain_class import PropertyDomainClass
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
    extract_concept_type_uris,
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
    class_uri_to_id: dict[str, UUID] = field(default_factory=dict)
    class_identifiers: set[str] = field(default_factory=set)
    property_identifiers: set[str] = field(default_factory=set)
    property_uris: set[str] = field(default_factory=set)
    property_uri_to_id: dict[str, UUID] = field(default_factory=dict)


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
            class_uri_to_id={c.uri: c.id for c in existing_classes if c.uri},
            class_identifiers={c.identifier for c in existing_classes},
            property_identifiers={p.identifier for p in existing_props},
            property_uris={p.uri for p in existing_props},
            property_uri_to_id={p.uri: p.id for p in existing_props},
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

            if not pm["domain_uris"]:
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
                    domain_class_uris=pm["domain_uris"],
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

        classes_created, superclass_warnings, class_uri_to_id = (
            await self._import_classes(
                project_id, analysis["classes"],
                existing.class_uris, existing.class_identifiers,
                existing.class_uri_to_id,
            )
        )

        # Compute class IDs from this file only (not all project classes)
        file_class_ids = {
            class_uri_to_id[cm["uri"]]
            for cm in analysis["classes"]
            if cm["uri"] in class_uri_to_id
        }
        await self._import_restrictions(
            analysis.get("restrictions", []),
            class_uri_to_id,
            file_class_ids,
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
            scheme_uri_to_id, class_uris, class_uri_to_id,
            existing.property_uri_to_id,
        )

        return ImportResultResponse(
            schemes_created=schemes_created,
            total_concepts_created=total_concepts,
            total_relationships_created=total_relationships,
            classes_created=classes_created,
            properties_created=properties_created,
            warnings=superclass_warnings + prop_warnings,
            validation_issues=validation_issues,
        )

    async def _import_classes(
        self, project_id: UUID, class_metadata: list[dict],
        existing_class_uris: set[str], existing_identifiers: set[str],
        existing_class_uri_to_id: dict[str, UUID] | None = None,
    ) -> tuple[list[ClassCreatedResponse], list[str], dict[str, UUID]]:
        """Create OntologyClass records and ClassSuperclass join rows.

        Returns created responses, unresolvable-superclass warnings, and
        class_uri_to_id map (existing + newly created).
        """
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

        if to_create:
            await self.db.flush()
            for ont_class, _ in to_create:
                await self.db.refresh(ont_class)

        # Build combined URI→id map: existing + newly created
        class_uri_to_id: dict[str, UUID] = dict(existing_class_uri_to_id or {})
        for ont_class, cm in to_create:
            class_uri_to_id[cm["uri"]] = ont_class.id

        # Wire ClassSuperclass edges for all classes in this import (new and existing).
        # Querying existing edges first prevents PK violations on re-import.
        all_class_ids = {
            class_uri_to_id[cm["uri"]]
            for cm in class_metadata
            if cm["uri"] in class_uri_to_id and cm.get("superclass_uris")
        }
        existing_edges: set[tuple[UUID, UUID]] = set()
        if all_class_ids:
            edges_result = await self.db.execute(
                select(ClassSuperclass.class_id, ClassSuperclass.superclass_id)
                .where(ClassSuperclass.class_id.in_(all_class_ids))
            )
            existing_edges = {(row.class_id, row.superclass_id) for row in edges_result}

        warnings: list[str] = []
        edges_added = False
        for cm in class_metadata:
            if cm["uri"] not in class_uri_to_id:
                continue
            class_id = class_uri_to_id[cm["uri"]]
            for superclass_uri in cm.get("superclass_uris", []):
                if superclass_uri in class_uri_to_id:
                    superclass_id = class_uri_to_id[superclass_uri]
                    if (class_id, superclass_id) not in existing_edges:
                        self.db.add(ClassSuperclass(
                            class_id=class_id,
                            superclass_id=superclass_id,
                        ))
                        existing_edges.add((class_id, superclass_id))
                        edges_added = True
                else:
                    warnings.append(
                        f"Superclass <{superclass_uri}> not found in project "
                        f"(referenced by <{cm['uri']}>)"
                    )
        if to_create or edges_added:
            await self.db.flush()

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
        return created, warnings, class_uri_to_id

    async def _import_restrictions(
        self,
        restrictions: list[dict],
        class_uri_to_id: dict[str, UUID],
        file_class_ids: set[UUID],
    ) -> None:
        """Replace ClassRestriction records for classes in the current file.

        Deletes existing restrictions for classes present in the file,
        then inserts the new set. Classes not in the file are untouched.
        """
        if not file_class_ids:
            return

        # Delete existing restrictions only for classes in this file
        await self.db.execute(
            delete(ClassRestriction).where(
                ClassRestriction.class_id.in_(file_class_ids)
            )
        )

        # Insert new restrictions
        for r in restrictions:
            class_id = class_uri_to_id.get(r["class_uri"])
            if class_id is None:
                continue
            self.db.add(ClassRestriction(
                class_id=class_id,
                on_property_uri=r["on_property_uri"],
                restriction_type=r["restriction_type"],
                value_uri=r["value_uri"],
            ))

        await self.db.flush()

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

            concept_types = extract_concept_type_uris(g, concept_uri)

            concept = Concept(
                scheme_id=scheme_id,
                pref_label=pref_label,
                identifier=identifier,
                definition=definition,
                scope_note=scope_note,
                alt_labels=alt_labels,
                concept_type_uris=concept_types,
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
        class_uri_to_id: dict[str, UUID] | None = None,
        existing_prop_uri_to_id: dict[str, UUID] | None = None,
    ) -> tuple[list[PropertyCreatedResponse], list[str]]:
        """Create Property records, skipping duplicates, resolving ranges."""
        warnings: list[str] = []
        known_ids = set(existing_prop_ids)
        known_uris = set(existing_prop_uris)
        uri_to_id = class_uri_to_id or {}
        prop_uri_to_id = existing_prop_uri_to_id or {}
        to_create: list[tuple[Property, list[str]]] = []  # (prop, domain_uris)

        for pm in property_metadata:
            identifier = pm["identifier"]
            if pm["uri"] in known_uris or identifier in known_ids:
                # Re-import: update domain classes for existing property
                if pm["uri"] in prop_uri_to_id:
                    domain_uris = sorted(pm["domain_uris"])
                    if domain_uris:
                        await self._update_property_domains(
                            prop_uri_to_id[pm["uri"]],
                            domain_uris,
                            uri_to_id,
                        )
                continue

            domain_uris = sorted(pm["domain_uris"])
            if not domain_uris:
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
                domain_class=domain_uris[0],
                range_scheme_id=range_scheme_id,
                range_datatype=range_datatype,
                range_class=range_class,
                cardinality=pm["cardinality"],
                property_type=prop_type,
                required=False,
                uri=pm["uri"],
            )
            self.db.add(prop)
            known_ids.add(identifier)
            known_uris.add(pm["uri"])
            to_create.append((prop, domain_uris))

        if to_create:
            await self.db.flush()
            for prop, _ in to_create:
                await self.db.refresh(prop)

            # Create PropertyDomainClass join rows
            for prop, d_uris in to_create:
                for d_uri in d_uris:
                    if d_uri in uri_to_id:
                        self.db.add(PropertyDomainClass(
                            property_id=prop.id,
                            class_id=uri_to_id[d_uri],
                        ))
            await self.db.flush()

        created: list[PropertyCreatedResponse] = []
        for prop, _ in to_create:
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

    async def _update_property_domains(
        self,
        property_id: UUID,
        domain_uris: list[str],
        class_uri_to_id: dict[str, UUID],
    ) -> None:
        """Replace PropertyDomainClass rows and update scalar for re-import."""
        if not domain_uris:
            return

        # Delete existing join rows
        await self.db.execute(
            delete(PropertyDomainClass).where(
                PropertyDomainClass.property_id == property_id
            )
        )

        # Insert new rows
        for uri in domain_uris:
            if uri in class_uri_to_id:
                self.db.add(PropertyDomainClass(
                    property_id=property_id,
                    class_id=class_uri_to_id[uri],
                ))

        # Update scalar to first sorted URI
        await self.db.execute(
            update(Property)
            .where(Property.id == property_id)
            .values(domain_class=domain_uris[0])
        )
        await self.db.flush()

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
