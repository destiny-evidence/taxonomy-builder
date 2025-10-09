"""API routes for taxonomy management."""

from fastapi import APIRouter, HTTPException, status

from taxonomy_builder.db.taxonomy_repository import InMemoryTaxonomyRepository
from taxonomy_builder.models.taxonomy import Taxonomy, TaxonomyCreate
from taxonomy_builder.services.taxonomy_service import TaxonomyService

router = APIRouter(prefix="/api/taxonomies", tags=["taxonomies"])

# Global repository instance (will be replaced with proper dependency injection later)
_repository = InMemoryTaxonomyRepository()
_taxonomy_service = TaxonomyService(repository=_repository)


@router.post("", response_model=Taxonomy, status_code=status.HTTP_201_CREATED)
async def create_taxonomy(taxonomy_data: TaxonomyCreate) -> Taxonomy:
    """Create a new taxonomy.

    Args:
        taxonomy_data: The taxonomy data to create

    Returns:
        The created taxonomy

    Raises:
        HTTPException: 409 if taxonomy with ID already exists
        HTTPException: 422 if validation fails
    """
    try:
        return _taxonomy_service.create_taxonomy(taxonomy_data)
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("", response_model=list[Taxonomy])
async def list_taxonomies() -> list[Taxonomy]:
    """List all taxonomies.

    Returns:
        List of all taxonomies
    """
    return _taxonomy_service.list_taxonomies()


@router.get("/{taxonomy_id}", response_model=Taxonomy)
async def get_taxonomy(taxonomy_id: str) -> Taxonomy:
    """Get a taxonomy by ID.

    Args:
        taxonomy_id: The ID of the taxonomy to retrieve

    Returns:
        The requested taxonomy

    Raises:
        HTTPException: 404 if taxonomy not found
    """
    try:
        return _taxonomy_service.get_taxonomy(taxonomy_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
