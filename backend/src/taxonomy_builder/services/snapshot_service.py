"""Service for building immutable project snapshots."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property
from taxonomy_builder.schemas.snapshot import (
    SnapshotClass,
    SnapshotConcept,
    SnapshotProjectMetadata,
    SnapshotProperty,
    SnapshotScheme,
    SnapshotVocabulary,
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

        return SnapshotVocabulary(
            project=self._build_project(project),
            concept_schemes=schemes,
            properties=properties,
            classes=classes,
        )

    def _build_project(self, project: Project) -> SnapshotProjectMetadata:
        return SnapshotProjectMetadata(
            id=project.id,
            name=project.name,
            description=project.description,
            namespace=project.namespace,
        )

    def _build_scheme(
        self, scheme: ConceptScheme, concepts: list[Concept]
    ) -> SnapshotScheme:
        return SnapshotScheme(
            id=scheme.id,
            title=scheme.title,
            description=scheme.description,
            uri=scheme.uri,
            concepts=[self._build_concept(c) for c in concepts],
        )

    def _build_concept(self, concept: Concept) -> SnapshotConcept:
        return SnapshotConcept(
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
        return SnapshotProperty(
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
            SnapshotClass(
                uri=cls.uri,
                label=cls.label,
                description=cls.comment,
            )
            for cls in ontology.classes
            if cls.uri in domain_uris
        ]
