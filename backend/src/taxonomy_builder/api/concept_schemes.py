"""API routes for concept scheme management."""

from fastapi import APIRouter, HTTPException, status

from taxonomy_builder.api.taxonomies import _taxonomy_service
from taxonomy_builder.db.concept_scheme_repository import InMemoryConceptSchemeRepository
from taxonomy_builder.models.concept_scheme import (
    ConceptScheme,
    ConceptSchemeCreate,
    ConceptSchemeUpdate,
)
from taxonomy_builder.services.concept_scheme_service import ConceptSchemeService

router = APIRouter(tags=["concept_schemes"])

# Global repository instance (will be replaced with proper dependency injection later)
_repository = InMemoryConceptSchemeRepository()
_concept_scheme_service = ConceptSchemeService(
    repository=_repository, taxonomy_service=_taxonomy_service
)


@router.post(
    "/api/taxonomies/{taxonomy_id}/schemes",
    response_model=ConceptScheme,
    status_code=status.HTTP_201_CREATED,
)
async def create_concept_scheme(
    taxonomy_id: str, scheme_data: ConceptSchemeCreate
) -> ConceptScheme:
    """Create a new concept scheme.

    Args:
        taxonomy_id: The ID of the taxonomy this scheme belongs to
        scheme_data: The concept scheme data to create

    Returns:
        The created concept scheme

    Raises:
        HTTPException: 404 if taxonomy not found
        HTTPException: 409 if scheme with ID already exists in taxonomy
        HTTPException: 422 if validation fails
    """
    try:
        return _concept_scheme_service.create_scheme(taxonomy_id, scheme_data)
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/api/taxonomies/{taxonomy_id}/schemes", response_model=list[ConceptScheme]
)
async def list_concept_schemes(taxonomy_id: str) -> list[ConceptScheme]:
    """List all concept schemes for a taxonomy.

    Args:
        taxonomy_id: The ID of the taxonomy

    Returns:
        List of all concept schemes for the taxonomy

    Raises:
        HTTPException: 404 if taxonomy not found
    """
    try:
        return _concept_scheme_service.list_schemes(taxonomy_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/api/schemes/{scheme_id}", response_model=ConceptScheme)
async def get_concept_scheme(scheme_id: str) -> ConceptScheme:
    """Get a concept scheme by ID.

    Args:
        scheme_id: The ID of the concept scheme to retrieve

    Returns:
        The requested concept scheme

    Raises:
        HTTPException: 404 if concept scheme not found
    """
    try:
        return _concept_scheme_service.get_scheme(scheme_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/api/schemes/{scheme_id}", response_model=ConceptScheme)
async def update_concept_scheme(
    scheme_id: str, update_data: ConceptSchemeUpdate
) -> ConceptScheme:
    """Update a concept scheme.

    Args:
        scheme_id: The ID of the concept scheme to update
        update_data: The fields to update

    Returns:
        The updated concept scheme

    Raises:
        HTTPException: 404 if concept scheme not found
    """
    try:
        return _concept_scheme_service.update_scheme(scheme_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/api/schemes/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_concept_scheme(scheme_id: str) -> None:
    """Delete a concept scheme.

    Args:
        scheme_id: The ID of the concept scheme to delete

    Raises:
        HTTPException: 404 if concept scheme not found
    """
    try:
        _concept_scheme_service.delete_scheme(scheme_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
