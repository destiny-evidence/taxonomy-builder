"""API routes for concepts."""

from fastapi import APIRouter, HTTPException, status

from taxonomy_builder.api.concept_schemes import (
    _concept_scheme_service,
)
from taxonomy_builder.api.concept_schemes import (
    _repository as scheme_repository,  # noqa: F401 - Imported for tests
)
from taxonomy_builder.db.concept_repository import InMemoryConceptRepository
from taxonomy_builder.models.concept import Concept, ConceptCreate, ConceptUpdate
from taxonomy_builder.services.concept_service import ConceptService

router = APIRouter(prefix="/api", tags=["concepts"])

# Initialize repository and service
concept_repository = InMemoryConceptRepository()
concept_service = ConceptService(
    repository=concept_repository, scheme_service=_concept_scheme_service
)


@router.post(
    "/schemes/{scheme_id}/concepts",
    response_model=Concept,
    status_code=status.HTTP_201_CREATED,
)
def create_concept(scheme_id: str, concept_data: ConceptCreate):
    """Create a new concept in a scheme."""
    try:
        return concept_service.create_concept(scheme_id, concept_data)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            )


@router.get("/schemes/{scheme_id}/concepts", response_model=list[Concept])
def list_concepts(scheme_id: str):
    """List all concepts for a scheme."""
    try:
        return concept_service.list_concepts(scheme_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/concepts/{concept_id}", response_model=Concept)
def get_concept(concept_id: str):
    """Get a concept by ID."""
    try:
        return concept_service.get_concept(concept_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/concepts/{concept_id}", response_model=Concept)
def update_concept(concept_id: str, update_data: ConceptUpdate):
    """Update a concept."""
    try:
        return concept_service.update_concept(concept_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/concepts/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept(concept_id: str):
    """Delete a concept."""
    try:
        concept_service.delete_concept(concept_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/concepts/{concept_id}/broader/{broader_id}", response_model=Concept)
def add_broader(concept_id: str, broader_id: str):
    """Add a broader concept relationship."""
    try:
        return concept_service.add_broader(concept_id, broader_id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            # Cycles and self-reference are business logic errors (400)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            )


@router.delete("/concepts/{concept_id}/broader/{broader_id}", response_model=Concept)
def remove_broader(concept_id: str, broader_id: str):
    """Remove a broader concept relationship."""
    try:
        return concept_service.remove_broader(concept_id, broader_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
