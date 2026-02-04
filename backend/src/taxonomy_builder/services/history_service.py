"""History service for querying change events."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.services.concept_scheme_service import SchemeNotFoundError
from taxonomy_builder.services.concept_service import ConceptNotFoundError


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
