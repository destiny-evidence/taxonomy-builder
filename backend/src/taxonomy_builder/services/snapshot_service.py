"""Service for building, validating, and diffing immutable project snapshots."""

from uuid import UUID

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property
from taxonomy_builder.schemas.snapshot import (
    DiffItem,
    DiffResult,
    FieldChange,
    ModifiedItem,
    SnapshotClass,
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotProperty,
    SnapshotScheme,
    SnapshotVocabulary,
    ValidationError,
    ValidationResult,
)
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.core_ontology_service import get_core_ontology
from taxonomy_builder.services.project_service import ProjectService


class SnapshotService:
    """Service for building complete project snapshots."""

    def __init__(
        self,
        db: AsyncSession,
        project_service: ProjectService,
        concept_service: ConceptService,
    ) -> None:
        self.db = db
        self._project_service = project_service
        self._concept_service = concept_service

    async def build_snapshot(self, project_id: UUID) -> SnapshotVocabulary:
        """Build an immutable snapshot of a project's vocabulary.

        Returns a SnapshotVocabulary with concept_schemes (with nested concepts),
        properties, and ontology classes referenced by those properties.
        """
        project = await self._project_service.get_project(project_id)

        schemes = []
        for scheme in project.schemes:
            concepts = await self._concept_service.list_concepts_for_scheme(
                scheme.id
            )
            schemes.append(self._build_scheme(scheme, concepts))

        properties = [self._build_property(p) for p in project.properties]

        domain_uris = {p.domain_class for p in project.properties}
        classes = self._build_classes(domain_uris)

        return SnapshotVocabulary.model_construct(
            project=self._build_project(project),
            concept_schemes=schemes,
            properties=properties,
            classes=classes,
        )

    def _build_project(self, project: Project) -> SnapshotProjectMetadata:
        return SnapshotProjectMetadata.model_construct(
            id=project.id,
            name=project.name,
            description=project.description,
            namespace=project.namespace,
        )

    def _build_scheme(
        self, scheme: ConceptScheme, concepts: list[Concept]
    ) -> SnapshotScheme:
        return SnapshotScheme.model_construct(
            id=scheme.id,
            title=scheme.title,
            description=scheme.description,
            uri=scheme.uri,
            concepts=[self._build_concept(c) for c in concepts],
        )

    def _build_concept(self, concept: Concept) -> SnapshotConcept:
        return SnapshotConcept.model_construct(
            id=concept.id,
            identifier=concept.identifier,
            uri=concept.uri,
            pref_label=concept.pref_label,
            definition=concept.definition,
            scope_note=concept.scope_note,
            alt_labels=list(concept.alt_labels),
            broader_ids=[b.id for b in concept.broader],
            related_ids=[r.id for r in concept.related],
        )

    def _build_property(self, prop: Property) -> SnapshotProperty:
        return SnapshotProperty.model_construct(
            id=prop.id,
            identifier=prop.identifier,
            uri=prop.uri,
            label=prop.label,
            description=prop.description,
            domain_class=prop.domain_class,
            range_scheme_id=prop.range_scheme_id,
            range_scheme_uri=prop.range_scheme.uri if prop.range_scheme else None,
            range_datatype=prop.range_datatype,
            cardinality=prop.cardinality,
            required=prop.required,
        )

    def _build_classes(self, domain_uris: set[str]) -> list[SnapshotClass]:
        if not domain_uris:
            return []

        ontology = get_core_ontology()
        return [
            SnapshotClass.model_construct(
                uri=cls.uri,
                label=cls.label,
                description=cls.comment,
            )
            for cls in ontology.classes
            if cls.uri in domain_uris
        ]


def validate_snapshot(snapshot: SnapshotVocabulary) -> ValidationResult:
    """Validate a snapshot is ready to publish.

    Runs Pydantic validators on the snapshot data, collecting all errors.
    """
    try:
        SnapshotVocabulary.model_validate(snapshot.model_dump(mode="json"))
        return ValidationResult(valid=True, errors=[])
    except PydanticValidationError as e:
        errors = []
        for err in e.errors():
            ctx = err.get("ctx", {})
            entity_id_str = ctx.get("entity_id")
            errors.append(
                ValidationError(
                    code=err["type"],
                    message=err["msg"],
                    entity_type=ctx.get("entity_type"),
                    entity_id=UUID(entity_id_str) if entity_id_str else None,
                    entity_label=ctx.get("entity_label"),
                )
            )
        return ValidationResult(valid=False, errors=errors)


def _field_changes(prev, curr, exclude: set[str]) -> list[FieldChange]:
    prev_data = prev.model_dump(exclude=exclude)
    curr_data = curr.model_dump(exclude=exclude)
    return [
        FieldChange(field=f, old=str(prev_data[f]), new=str(curr_data[f]))
        for f in prev_data
        if prev_data[f] != curr_data[f]
    ]


def compute_diff(
    previous: SnapshotVocabulary | None,
    current: SnapshotVocabulary,
) -> DiffResult:
    """Diff two snapshots, returning added/modified/removed items."""
    prev_schemes = {s.id: s for s in previous.concept_schemes} if previous else {}
    curr_schemes = {s.id: s for s in current.concept_schemes}
    prev_props = {p.id: p for p in previous.properties} if previous else {}
    curr_props = {p.id: p for p in current.properties}
    prev_classes = {c.uri: c for c in previous.classes} if previous else {}
    curr_classes = {c.uri: c for c in current.classes}

    # Categorise changes
    added_schemes = [
        curr_schemes[scheme_id] for scheme_id in curr_schemes.keys() - prev_schemes.keys()
    ]
    removed_schemes = [
        prev_schemes[scheme_id] for scheme_id in prev_schemes.keys() - curr_schemes.keys()
    ]
    modified_schemes = [
        (
            prev_schemes[scheme_id],
            curr_schemes[scheme_id],
            {concept.id: concept for concept in prev_schemes[scheme_id].concepts},
            {concept.id: concept for concept in curr_schemes[scheme_id].concepts},
        )
        for scheme_id in prev_schemes.keys() & curr_schemes.keys()
    ]
    added_properties = [curr_props[pid] for pid in curr_props.keys() - prev_props.keys()]
    removed_properties = [prev_props[pid] for pid in prev_props.keys() - curr_props.keys()]
    modified_properties = [
        (prev_props[pid], curr_props[pid]) for pid in prev_props.keys() & curr_props.keys()
    ]
    added_classes = [curr_classes[uri] for uri in curr_classes.keys() - prev_classes.keys()]
    removed_classes = [prev_classes[uri] for uri in prev_classes.keys() - curr_classes.keys()]

    added = (
        # New schemes
        [
            DiffItem(id=scheme.id, label=scheme.title, entity_type="scheme")
            for scheme in added_schemes
        ]
        # Concepts in new schemes
        + [
            DiffItem(id=concept.id, label=concept.pref_label, entity_type="concept")
            for scheme in added_schemes
            for concept in scheme.concepts
        ]
        # New concepts in existing schemes
        + [
            DiffItem(
                id=concept_id, label=curr_concepts[concept_id].pref_label, entity_type="concept"
            )
            for _, _, prev_concepts, curr_concepts in modified_schemes
            for concept_id in curr_concepts.keys() - prev_concepts.keys()
        ]
        # New properties
        + [
            DiffItem(id=property.id, label=property.label, entity_type="property")
            for property in added_properties
        ]
        # New classes
        + [DiffItem(uri=cls.uri, label=cls.label, entity_type="class") for cls in added_classes]
    )

    removed = (
        # Removed schemes
        [
            DiffItem(id=scheme.id, label=scheme.title, entity_type="scheme")
            for scheme in removed_schemes
        ]
        # Concepts in removed schemes
        + [
            DiffItem(id=concept.id, label=concept.pref_label, entity_type="concept")
            for scheme in removed_schemes
            for concept in scheme.concepts
        ]
        # Removed concepts in existing schemes
        + [
            DiffItem(
                id=concept_id, label=prev_concepts[concept_id].pref_label, entity_type="concept"
            )
            for _, _, prev_concepts, curr_concepts in modified_schemes
            for concept_id in prev_concepts.keys() - curr_concepts.keys()
        ]
        # Removed properties
        + [
            DiffItem(id=property.id, label=property.label, entity_type="property")
            for property in removed_properties
        ]
        # Removed classes
        + [
            DiffItem(uri=cls.uri, label=cls.label, entity_type="class")
            for cls in removed_classes
        ]
    )

    modified = (
        # Modified scheme metadata
        [
            ModifiedItem(
                id=curr_scheme.id,
                label=curr_scheme.title,
                entity_type="scheme",
                changes=changes,
            )
            for prev_scheme, curr_scheme, _, _ in modified_schemes
            if (
                changes := _field_changes(
                    prev_scheme, curr_scheme, {"id", "concepts"}
                )
            )
        ]
        # Modified concepts in existing schemes
        + [
            ModifiedItem(
                id=concept_id,
                label=curr_concepts[concept_id].pref_label,
                entity_type="concept",
                changes=changes,
            )
            for _, _, prev_concepts, curr_concepts in modified_schemes
            for concept_id in prev_concepts.keys() & curr_concepts.keys()
            if (
                changes := _field_changes(
                    prev_concepts[concept_id], curr_concepts[concept_id], {"id"}
                )
            )
        ]
        # Modified properties
        + [
            ModifiedItem(
                id=curr_property.id,
                label=curr_property.label,
                entity_type="property",
                changes=changes,
            )
            for prev_property, curr_property in modified_properties
            if (
                changes := _field_changes(
                    prev_property, curr_property, {"id"}
                )
            )
        ]
    )

    return DiffResult(added=added, modified=modified, removed=removed)
