"""Service for building immutable project snapshots."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property
from taxonomy_builder.services.core_ontology_service import get_core_ontology


class ProjectNotFoundError(Exception):
    """Raised when a project is not found."""

    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        super().__init__(f"Project with id '{project_id}' not found")


class SnapshotService:
    """Service for building complete project snapshots."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def build_snapshot(self, project_id: UUID) -> dict:
        """Build an immutable snapshot of a project's vocabulary.

        Returns a dict with concept_schemes (with nested concepts),
        properties, and ontology classes referenced by those properties.
        """
        project = await self._get_project(project_id)

        scheme_dicts = []
        for scheme in project.schemes:
            concepts = await self._get_concepts_for_scheme(scheme.id)
            scheme_dicts.append(self._build_scheme_dict(scheme, concepts))

        property_dicts = [self._build_property_dict(p) for p in project.properties]

        domain_uris = {p.domain_class for p in project.properties}
        class_dicts = self._build_class_dicts(domain_uris)

        return {
            "concept_schemes": scheme_dicts,
            "properties": property_dicts,
            "classes": class_dicts,
        }

    async def _get_project(self, project_id: UUID) -> Project:
        """Load project with schemes and properties."""
        result = await self.db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.schemes),
                selectinload(Project.properties).selectinload(Property.project),
            )
            .execution_options(populate_existing=True)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    async def _get_concepts_for_scheme(self, scheme_id: UUID) -> list[Concept]:
        """Get all concepts for a scheme with relationships loaded."""
        result = await self.db.execute(
            select(Concept)
            .where(Concept.scheme_id == scheme_id)
            .options(
                selectinload(Concept.broader),
                selectinload(Concept.scheme),
                selectinload(Concept._related_as_subject),
                selectinload(Concept._related_as_object),
            )
            .execution_options(populate_existing=True)
        )
        return list(result.scalars().all())

    def _build_scheme_dict(
        self, scheme: ConceptScheme, concepts: list[Concept]
    ) -> dict:
        """Build a scheme snapshot dict with nested concepts."""
        return {
            "id": str(scheme.id),
            "title": scheme.title,
            "description": scheme.description,
            "uri": scheme.uri,
            "concepts": [self._build_concept_dict(c) for c in concepts],
        }

    def _build_concept_dict(self, concept: Concept) -> dict:
        """Build a concept snapshot dict."""
        return {
            "id": str(concept.id),
            "identifier": concept.identifier,
            "uri": concept.uri,
            "pref_label": concept.pref_label,
            "definition": concept.definition,
            "scope_note": concept.scope_note,
            "alt_labels": list(concept.alt_labels),
            "broader_ids": [str(b.id) for b in concept.broader],
            "related_ids": [str(r.id) for r in concept.related],
        }

    def _build_property_dict(self, prop: Property) -> dict:
        """Build a property snapshot dict."""
        return {
            "id": str(prop.id),
            "identifier": prop.identifier,
            "uri": prop.uri,
            "label": prop.label,
            "description": prop.description,
            "domain_class": prop.domain_class,
            "range_scheme_id": str(prop.range_scheme_id) if prop.range_scheme_id else None,
            "range_datatype": prop.range_datatype,
            "cardinality": prop.cardinality,
            "required": prop.required,
        }

    def _build_class_dicts(self, domain_uris: set[str]) -> list[dict]:
        """Build class dicts for ontology classes referenced by properties."""
        if not domain_uris:
            return []

        ontology = get_core_ontology()
        return [
            {
                "uri": cls.uri,
                "label": cls.label,
                "description": cls.comment,
            }
            for cls in ontology.classes
            if cls.uri in domain_uris
        ]
