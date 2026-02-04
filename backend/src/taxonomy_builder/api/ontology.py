"""Ontology API endpoints."""

from fastapi import APIRouter

from taxonomy_builder.schemas.ontology import (
    CoreOntologyResponse,
    OntologyClass,
    OntologyProperty,
)
from taxonomy_builder.services.core_ontology_service import get_core_ontology

router = APIRouter(prefix="/api/ontology", tags=["ontology"])


@router.get("", response_model=CoreOntologyResponse)
async def get_ontology() -> CoreOntologyResponse:
    """Get the core ontology classes and properties.

    Returns the classes, object properties, and datatype properties
    from the cached core ontology (loaded at startup).
    """
    ontology = get_core_ontology()

    return CoreOntologyResponse(
        classes=[
            OntologyClass(
                uri=c.uri,
                label=c.label,
                comment=c.comment,
            )
            for c in ontology.classes
        ],
        object_properties=[
            OntologyProperty(
                uri=p.uri,
                label=p.label,
                comment=p.comment,
                domain=p.domain,
                range=p.range,
                property_type=p.property_type,
            )
            for p in ontology.object_properties
        ],
        datatype_properties=[
            OntologyProperty(
                uri=p.uri,
                label=p.label,
                comment=p.comment,
                domain=p.domain,
                range=p.range,
                property_type=p.property_type,
            )
            for p in ontology.datatype_properties
        ],
    )
