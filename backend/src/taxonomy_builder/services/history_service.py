"""History service for querying change events."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property
from taxonomy_builder.services.concept_scheme_service import SchemeNotFoundError
from taxonomy_builder.services.concept_service import ConceptNotFoundError
from taxonomy_builder.services.project_service import ProjectNotFoundError
from taxonomy_builder.services.property_service import PropertyNotFoundError


class HistoryService:
    """Service for querying change event history."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_scheme_history(
        self,
        scheme_id: UUID,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ChangeEvent]:
        """Get history of changes for a scheme."""
        result = await self.db.execute(
            select(ConceptScheme).where(ConceptScheme.id == scheme_id)
        )
        if result.scalar_one_or_none() is None:
            raise SchemeNotFoundError(scheme_id)

        query = (
            select(ChangeEvent)
            .options(joinedload(ChangeEvent.user))
            .where(ChangeEvent.scheme_id == scheme_id)
            .order_by(ChangeEvent.timestamp.desc())
        )
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_concept_history(self, concept_id: UUID) -> list[ChangeEvent]:
        """Get history of changes for a specific concept."""
        result = await self.db.execute(
            select(Concept).where(Concept.id == concept_id)
        )
        if result.scalar_one_or_none() is None:
            raise ConceptNotFoundError(concept_id)

        result = await self.db.execute(
            select(ChangeEvent)
            .options(joinedload(ChangeEvent.user))
            .where(
                ChangeEvent.entity_type == "concept",
                ChangeEvent.entity_id == concept_id,
            )
            .order_by(ChangeEvent.timestamp.desc())
        )
        return list(result.scalars().all())

    async def get_project_history(
        self,
        project_id: UUID,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ChangeEvent]:
        """Get history of changes for a project."""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        if result.scalar_one_or_none() is None:
            raise ProjectNotFoundError(project_id)

        query = (
            select(ChangeEvent)
            .options(joinedload(ChangeEvent.user))
            .where(ChangeEvent.project_id == project_id)
            .order_by(ChangeEvent.timestamp.desc())
        )
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_property_history(self, property_id: UUID) -> list[ChangeEvent]:
        """Get history of changes for a specific property."""
        result = await self.db.execute(
            select(Property).where(Property.id == property_id)
        )
        if result.scalar_one_or_none() is None:
            raise PropertyNotFoundError(property_id)

        result = await self.db.execute(
            select(ChangeEvent)
            .options(joinedload(ChangeEvent.user))
            .where(
                ChangeEvent.entity_type == "property",
                ChangeEvent.entity_id == property_id,
            )
            .order_by(ChangeEvent.timestamp.desc())
        )
        return list(result.scalars().all())
