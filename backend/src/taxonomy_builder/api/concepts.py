"""Concept API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.database import get_db
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.schemas.concept import ConceptCreate, ConceptRead, ConceptUpdate
from taxonomy_builder.services.concept_service import (
    BroaderRelationshipExistsError,
    BroaderRelationshipNotFoundError,
    ConceptNotFoundError,
    ConceptService,
    SchemeNotFoundError,
)

# Router for scheme-scoped concept operations
scheme_concepts_router = APIRouter(prefix="/api/schemes", tags=["concepts"])

# Router for direct concept operations
concepts_router = APIRouter(prefix="/api/concepts", tags=["concepts"])


class AddBroaderRequest(BaseModel):
    """Request body for adding a broader relationship."""

    broader_concept_id: UUID


def get_concept_service(db: AsyncSession = Depends(get_db)) -> ConceptService:
    """Dependency that provides a ConceptService instance."""
    return ConceptService(db)


@scheme_concepts_router.get("/{scheme_id}/concepts", response_model=list[ConceptRead])
async def list_concepts(
    scheme_id: UUID,
    service: ConceptService = Depends(get_concept_service),
) -> list[Concept]:
    """List all concepts for a scheme, ordered alphabetically."""
    try:
        return await service.list_concepts_for_scheme(scheme_id)
    except SchemeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@scheme_concepts_router.post(
    "/{scheme_id}/concepts",
    response_model=ConceptRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_concept(
    scheme_id: UUID,
    concept_in: ConceptCreate,
    service: ConceptService = Depends(get_concept_service),
) -> Concept:
    """Create a new concept in a scheme."""
    try:
        return await service.create_concept(scheme_id, concept_in)
    except SchemeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@scheme_concepts_router.get("/{scheme_id}/tree")
async def get_tree(
    scheme_id: UUID,
    service: ConceptService = Depends(get_concept_service),
) -> list[dict[str, Any]]:
    """Get the concept tree for a scheme as a DAG.

    Concepts with multiple parents appear under each parent.
    """
    try:
        return await service.get_tree(scheme_id)
    except SchemeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@concepts_router.get("/{concept_id}", response_model=ConceptRead)
async def get_concept(
    concept_id: UUID,
    service: ConceptService = Depends(get_concept_service),
) -> Concept:
    """Get a single concept by ID."""
    try:
        return await service.get_concept(concept_id)
    except ConceptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@concepts_router.put("/{concept_id}", response_model=ConceptRead)
async def update_concept(
    concept_id: UUID,
    concept_in: ConceptUpdate,
    service: ConceptService = Depends(get_concept_service),
) -> Concept:
    """Update an existing concept."""
    try:
        return await service.update_concept(concept_id, concept_in)
    except ConceptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@concepts_router.delete("/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_concept(
    concept_id: UUID,
    service: ConceptService = Depends(get_concept_service),
) -> None:
    """Delete a concept."""
    try:
        await service.delete_concept(concept_id)
    except ConceptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@concepts_router.post("/{concept_id}/broader", status_code=status.HTTP_201_CREATED)
async def add_broader(
    concept_id: UUID,
    request: AddBroaderRequest,
    service: ConceptService = Depends(get_concept_service),
) -> dict[str, str]:
    """Add a broader relationship to a concept."""
    try:
        await service.add_broader(concept_id, request.broader_concept_id)
        return {"status": "created"}
    except ConceptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BroaderRelationshipExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@concepts_router.delete(
    "/{concept_id}/broader/{broader_concept_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_broader(
    concept_id: UUID,
    broader_concept_id: UUID,
    service: ConceptService = Depends(get_concept_service),
) -> None:
    """Remove a broader relationship from a concept."""
    try:
        await service.remove_broader(concept_id, broader_concept_id)
    except BroaderRelationshipNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
