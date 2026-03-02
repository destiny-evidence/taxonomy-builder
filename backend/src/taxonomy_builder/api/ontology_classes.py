"""Ontology class API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from taxonomy_builder.api.dependencies import get_ontology_class_service
from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.schemas.ontology_class import (
    OntologyClassCreate,
    OntologyClassRead,
    OntologyClassUpdate,
)
from taxonomy_builder.services.ontology_class_service import (
    OntologyClassIdentifierExistsError,
    OntologyClassReferencedByPropertyError,
    OntologyClassService,
    OntologyClassURIExistsError,
    ProjectNamespaceRequiredError,
)
from taxonomy_builder.services.project_service import ProjectNotFoundError

# Router for project-scoped ontology class operations
project_ontology_classes_router = APIRouter(prefix="/api/projects", tags=["ontology_classes"])

# Router for direct ontology class operations
ontology_classes_router = APIRouter(prefix="/api/classes", tags=["ontology_classes"])


@project_ontology_classes_router.get(
    "/{project_id}/classes", response_model=list[OntologyClassRead]
)
async def list_ontology_classes(
    project_id: UUID,
    service: OntologyClassService = Depends(get_ontology_class_service),
) -> list[OntologyClass]:
    """List all ontology classes for a project."""
    try:
        return await service.list_ontology_classes(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@project_ontology_classes_router.post(
    "/{project_id}/classes",
    response_model=OntologyClassRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_ontology_class(
    project_id: UUID,
    ontology_class_in: OntologyClassCreate,
    service: OntologyClassService = Depends(get_ontology_class_service),
) -> OntologyClass:
    """Create a new ontology class in a project."""
    try:
        return await service.create_ontology_class(project_id, ontology_class_in)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProjectNamespaceRequiredError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OntologyClassIdentifierExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except OntologyClassURIExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@ontology_classes_router.get("/{class_id}", response_model=OntologyClassRead)
async def get_ontology_class(
    class_id: UUID,
    service: OntologyClassService = Depends(get_ontology_class_service),
) -> OntologyClass:
    """Get a single ontology class by ID."""
    ontology_class = await service.get_ontology_class(class_id)
    if ontology_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology class with id '{class_id}' not found",
        )
    return ontology_class


@ontology_classes_router.put("/{class_id}", response_model=OntologyClassRead)
async def update_ontology_class(
    class_id: UUID,
    ontology_class_in: OntologyClassUpdate,
    service: OntologyClassService = Depends(get_ontology_class_service),
) -> OntologyClass:
    """Update an existing ontology class."""
    try:
        ontology_class = await service.update_ontology_class(class_id, ontology_class_in)
        if ontology_class is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ontology class with id '{class_id}' not found",
            )
        return ontology_class
    except OntologyClassIdentifierExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@ontology_classes_router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ontology_class(
    class_id: UUID,
    service: OntologyClassService = Depends(get_ontology_class_service),
) -> None:
    """Delete an ontology class."""
    try:
        deleted = await service.delete_ontology_class(class_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ontology class with id '{class_id}' not found",
            )
    except OntologyClassReferencedByPropertyError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
