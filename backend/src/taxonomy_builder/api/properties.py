"""Property API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from taxonomy_builder.api.dependencies import get_property_service
from taxonomy_builder.models.property import Property
from taxonomy_builder.schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from taxonomy_builder.services.project_service import ProjectNotFoundError
from taxonomy_builder.services.property_service import (
    DomainClassNotFoundError,
    InvalidRangeError,
    PropertyIdentifierExistsError,
    PropertyService,
    PropertyURIExistsError,
    SchemeNotInProjectError,
)

# Router for project-scoped property operations
project_properties_router = APIRouter(prefix="/api/projects", tags=["properties"])

# Router for direct property operations
properties_router = APIRouter(prefix="/api/properties", tags=["properties"])


@project_properties_router.get(
    "/{project_id}/properties", response_model=list[PropertyRead]
)
async def list_properties(
    project_id: UUID,
    service: PropertyService = Depends(get_property_service),
) -> list[Property]:
    """List all properties for a project."""
    try:
        return await service.list_properties(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@project_properties_router.post(
    "/{project_id}/properties",
    response_model=PropertyRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_property(
    project_id: UUID,
    property_in: PropertyCreate,
    service: PropertyService = Depends(get_property_service),
) -> Property:
    """Create a new property in a project."""
    try:
        return await service.create_property(project_id, property_in)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DomainClassNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidRangeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SchemeNotInProjectError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PropertyIdentifierExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PropertyURIExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@properties_router.get("/{property_id}", response_model=PropertyRead)
async def get_property(
    property_id: UUID,
    service: PropertyService = Depends(get_property_service),
) -> Property:
    """Get a single property by ID."""
    prop = await service.get_property(property_id)
    if prop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with id '{property_id}' not found",
        )
    return prop


@properties_router.put("/{property_id}", response_model=PropertyRead)
async def update_property(
    property_id: UUID,
    property_in: PropertyUpdate,
    service: PropertyService = Depends(get_property_service),
) -> Property:
    """Update an existing property."""
    try:
        prop = await service.update_property(property_id, property_in)
        if prop is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property with id '{property_id}' not found",
            )
        return prop
    except DomainClassNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidRangeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SchemeNotInProjectError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@properties_router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: UUID,
    service: PropertyService = Depends(get_property_service),
) -> None:
    """Delete a property."""
    deleted = await service.delete_property(property_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with id '{property_id}' not found",
        )
