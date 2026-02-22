"""Service for building, validating, and diffing immutable project snapshots."""

from uuid import UUID

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.ontology_class import OntologyClass
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
        properties, and ontology classes.
        """
        project = await self._project_service.get_project(project_id)

        schemes = []
        for scheme in project.schemes:
            scheme.concepts = await self._concept_service.list_concepts_for_scheme(scheme.id)
            schemes.append(
                SnapshotScheme.from_scheme(scheme)
            )

        properties = [SnapshotProperty.from_property(p) for p in project.properties]
        classes = [
            SnapshotClass.from_class(ontology_class) for ontology_class in project.ontology_classes
        ]

        return SnapshotVocabulary.model_construct(
            project=SnapshotProjectMetadata.from_project(project),
            concept_schemes=schemes,
            properties=properties,
            classes=classes,
        )


def validate_snapshot(snapshot: SnapshotVocabulary) -> ValidationResult:
    """Validate a snapshot is ready to publish.

    Runs Pydantic validators on the snapshot data, then checks
    referential integrity (broader/related/range_scheme links).
    """
    errors: list[ValidationError] = []

    try:
        SnapshotVocabulary.model_validate(snapshot.model_dump(mode="json"))
    except PydanticValidationError as e:
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

    errors.extend(_validate_references(snapshot))
    return ValidationResult(valid=len(errors) == 0, errors=errors)


def _validate_references(snapshot: SnapshotVocabulary) -> list[ValidationError]:
    """Check that all broader/related/range_scheme references resolve."""
    errors: list[ValidationError] = []

    all_concept_ids = {
        concept.id for scheme in snapshot.concept_schemes for concept in (scheme.concepts or [])
    }
    scheme_ids = {scheme.id for scheme in snapshot.concept_schemes}

    for scheme in snapshot.concept_schemes:
        for concept in scheme.concepts or []:
            for bid in concept.broader_ids or []:
                if bid not in all_concept_ids:
                    errors.append(
                        ValidationError(
                            code="broken_broader_ref",
                            message=f"Concept '{concept.pref_label}' has a broader reference to a non-existent concept.",
                            entity_type="concept",
                            entity_id=concept.id,
                            entity_label=concept.pref_label,
                        )
                    )
            for rid in concept.related_ids or []:
                if rid not in all_concept_ids:
                    errors.append(
                        ValidationError(
                            code="broken_related_ref",
                            message=f"Concept '{concept.pref_label}' has a related reference to a non-existent concept.",
                            entity_type="concept",
                            entity_id=concept.id,
                            entity_label=concept.pref_label,
                        )
                    )

    class_uris = {cls.uri for cls in snapshot.classes if cls.uri}

    for prop in snapshot.properties or []:
        if prop.range_scheme_id and prop.range_scheme_id not in scheme_ids:
            errors.append(
                ValidationError(
                    code="broken_range_scheme_ref",
                    message=f"property '{prop.label}' references a non-existent scheme.",
                    entity_type="property",
                    entity_id=prop.id,
                    entity_label=prop.label,
                )
            )
        if prop.domain_class and prop.domain_class not in class_uris:
            errors.append(
                ValidationError(
                    code="broken_domain_class_ref",
                    message=(
                        f"property '{prop.label}' references domain class"
                        f" '{prop.domain_class}' which is not in the"
                        " project's ontology classes."
                    ),
                    entity_type="property",
                    entity_id=prop.id,
                    entity_label=prop.label,
                )
            )
        if prop.range_class and prop.range_class not in class_uris:
            errors.append(
                ValidationError(
                    code="broken_range_class_ref",
                    message=(
                        f"property '{prop.label}' references range class"
                        f" '{prop.range_class}' which is not in the"
                        " project's ontology classes."
                    ),
                    entity_type="property",
                    entity_id=prop.id,
                    entity_label=prop.label,
                )
            )

    return errors


def _resolve_change(field: str, old, new, labels: dict[UUID, str]) -> FieldChange:
    """Turn a raw field diff into a FieldChange, resolving IDs to labels."""
    if field.endswith("_ids"):
        return FieldChange(
            field=field.removesuffix("_ids"),
            old=", ".join(sorted(labels.get(v, str(v)) for v in old)) if old else "",
            new=", ".join(sorted(labels.get(v, str(v)) for v in new)) if new else "",
        )
    if field.endswith("_id"):
        return FieldChange(
            field=field.removesuffix("_id"),
            old=labels.get(old, str(old)) if old else None,
            new=labels.get(new, str(new)) if new else None,
        )
    return FieldChange(field=field, old=str(old), new=str(new))


def _field_changes(
    prev,
    curr,
    exclude: set[str],
    labels: dict[UUID, str] | None = None,
) -> list[FieldChange]:
    prev_data = prev.model_dump(exclude=exclude)
    curr_data = curr.model_dump(exclude=exclude)
    return [
        _resolve_change(f, prev_data[f], curr_data[f], labels or {})
        for f in prev_data
        if prev_data[f] != curr_data[f]
    ]


def compute_diff(
    previous: SnapshotVocabulary | None,
    current: SnapshotVocabulary,
) -> DiffResult:
    """Diff two snapshots, returning added/modified/removed items."""
    # Build label lookup for resolving IDs in relationship fields
    labels: dict[UUID, str] = {}
    for snap in (previous, current):
        if snap is None:
            continue
        for scheme in snap.concept_schemes:
            labels[scheme.id] = scheme.title
            for concept in scheme.concepts or []:
                labels[concept.id] = concept.pref_label

    prev_schemes = {s.id: s for s in previous.concept_schemes} if previous else {}
    curr_schemes = {s.id: s for s in current.concept_schemes}
    prev_props = {p.id: p for p in previous.properties} if previous else {}
    curr_props = {p.id: p for p in current.properties}
    prev_classes = {c.id: c for c in previous.classes} if previous else {}
    curr_classes = {c.id: c for c in current.classes}

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
    added_classes = [curr_classes[cid] for cid in curr_classes.keys() - prev_classes.keys()]
    removed_classes = [prev_classes[cid] for cid in prev_classes.keys() - curr_classes.keys()]
    modified_classes = [
        (prev_classes[cid], curr_classes[cid]) for cid in prev_classes.keys() & curr_classes.keys()
    ]

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
            DiffItem(id=prop.id, label=prop.label, entity_type="property")
            for prop in added_properties
        ]
        # New classes
        + [DiffItem(id=cls.id, label=cls.label, entity_type="class") for cls in added_classes]
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
            DiffItem(id=prop.id, label=prop.label, entity_type="property")
            for prop in removed_properties
        ]
        # Removed classes
        + [DiffItem(id=cls.id, label=cls.label, entity_type="class") for cls in removed_classes]
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
            if (changes := _field_changes(prev_scheme, curr_scheme, {"id", "concepts"}))
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
                    prev_concepts[concept_id], curr_concepts[concept_id], {"id"}, labels
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
            if (changes := _field_changes(prev_property, curr_property, {"id"}, labels))
        ]
        # Modified classes
        + [
            ModifiedItem(
                id=curr_cls.id,
                label=curr_cls.label,
                entity_type="class",
                changes=changes,
            )
            for prev_cls, curr_cls in modified_classes
            if (changes := _field_changes(prev_cls, curr_cls, {"id"}))
        ]
    )

    return DiffResult(added=added, modified=modified, removed=removed)
