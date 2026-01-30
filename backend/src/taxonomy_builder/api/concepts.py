"""Concept API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from taxonomy_builder.api.dependencies import get_concept_service
from taxonomy_builder.models.concept import Concept
from taxonomy_builder.schemas.concept import (
    ConceptCreate,
    ConceptMoveRequest,
    ConceptRead,
    ConceptUpdate,
)
from taxonomy_builder.services.concept_service import (
    BroaderRelationshipExistsError,
    BroaderRelationshipNotFoundError,
    ConceptNotFoundError,
    ConceptService,
    CycleDetectedError,
    RelatedRelationshipExistsError,
    RelatedRelationshipNotFoundError,
    RelatedSameSchemeError,
    RelatedSelfReferenceError,
    SchemeNotFoundError,
    SelfReferenceError,
)

# Router for scheme-scoped concept operations
scheme_concepts_router = APIRouter(prefix="/api/schemes", tags=["concepts"])

# Router for direct concept operations
concepts_router = APIRouter(prefix="/api/concepts", tags=["concepts"])


class AddBroaderRequest(BaseModel):
    """Request body for adding a broader relationship."""

    broader_concept_id: UUID


class AddRelatedRequest(BaseModel):
    """Request body for adding a related relationship."""

    related_concept_id: UUID


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
    except (ConceptNotFoundError, BroaderRelationshipNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@concepts_router.post("/{concept_id}/related", status_code=status.HTTP_201_CREATED)
async def add_related(
    concept_id: UUID,
    request: AddRelatedRequest,
    service: ConceptService = Depends(get_concept_service),
) -> dict[str, str]:
    """Add a related relationship between two concepts.

    The relationship is symmetric - if A is related to B, B is also related to A.
    Both concepts must be in the same scheme.
    """
    try:
        await service.add_related(concept_id, request.related_concept_id)
        return {"status": "created"}
    except ConceptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RelatedRelationshipExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RelatedSelfReferenceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RelatedSameSchemeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@concepts_router.delete(
    "/{concept_id}/related/{related_concept_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_related(
    concept_id: UUID,
    related_concept_id: UUID,
    service: ConceptService = Depends(get_concept_service),
) -> None:
    """Remove a related relationship between two concepts.

    Works regardless of which concept is passed first (symmetric).
    """
    try:
        await service.remove_related(concept_id, related_concept_id)
    except (ConceptNotFoundError, RelatedRelationshipNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@concepts_router.post("/{concept_id}/move", response_model=ConceptRead)
async def move_concept(
    concept_id: UUID,
    request: ConceptMoveRequest,
    service: ConceptService = Depends(get_concept_service),
) -> Concept:
    """Move a concept to a new parent or to root level.

    - new_parent_id=null: Move to root (remove from previous_parent)
    - previous_parent_id=null: Add as additional parent (polyhierarchy)
    - Both specified: Replace previous_parent with new_parent
    """
    try:
        return await service.move_concept(
            concept_id,
            request.new_parent_id,
            request.previous_parent_id,
        )
    except ConceptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SelfReferenceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CycleDetectedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
