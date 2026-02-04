"""History API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from taxonomy_builder.api.dependencies import CurrentUser
from taxonomy_builder.database import get_db
from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.schemas.history import ChangeEventRead

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/schemes/{scheme_id}/history", response_model=list[ChangeEventRead])
async def get_scheme_history(
    scheme_id: UUID,
    current_user: CurrentUser,
    limit: int | None = None,
    offset: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ChangeEvent]:
    """Get history of changes for a scheme."""
    # Verify scheme exists
    result = await db.execute(
        select(ConceptScheme).where(ConceptScheme.id == scheme_id)
    )
    scheme = result.scalar_one_or_none()
    if scheme is None:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Get change events for this scheme with user info
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
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/concepts/{concept_id}/history", response_model=list[ChangeEventRead])
async def get_concept_history(
    concept_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[ChangeEvent]:
    """Get history of changes for a specific concept."""
    # Verify concept exists
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalar_one_or_none()
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Get change events for this concept with user info
    result = await db.execute(
        select(ChangeEvent)
        .options(joinedload(ChangeEvent.user))
        .where(
            ChangeEvent.entity_type == "concept",
            ChangeEvent.entity_id == concept_id,
        )
        .order_by(ChangeEvent.timestamp.desc())
    )
    return list(result.scalars().all())
