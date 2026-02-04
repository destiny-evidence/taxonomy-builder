"""Pydantic schemas for Ontology API responses."""

from typing import Literal

from pydantic import BaseModel


class OntologyClass(BaseModel):
    """Schema for an OWL class from the core ontology."""

    uri: str
    label: str
    comment: str | None


class OntologyProperty(BaseModel):
    """Schema for an OWL property from the core ontology."""

    uri: str
    label: str
    comment: str | None
    domain: list[str]
    range: list[str]
    property_type: Literal["object", "datatype"]


class CoreOntologyResponse(BaseModel):
    """Schema for the complete core ontology response."""

    classes: list[OntologyClass]
    object_properties: list[OntologyProperty]
    datatype_properties: list[OntologyProperty]
