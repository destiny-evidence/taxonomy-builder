"""History service for querying change events."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from taxonomy_builder.models.change_event import ChangeEvent


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
        """Get history of changes for a scheme.

        Returns an empty list if the scheme has no history (including non-existent IDs).
        """
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
        """Get history of changes for a specific concept.

        Returns an empty list if the concept has no history (including non-existent IDs).
        """
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
        """Get history of changes for a project.

        Returns an empty list if the project has no history (including non-existent IDs).
        """
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
        """Get history of changes for a specific property.

        Returns an empty list if the property has no history (including non-existent IDs).
        """
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
