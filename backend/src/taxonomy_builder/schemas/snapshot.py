"""Pydantic schemas for immutable project snapshots.

These models define the contract for snapshot data stored in
PublishedVersion.snapshot (JSONB). Use SnapshotVocabulary.model_validate()
to deserialize from JSONB, and .model_dump() to serialize for storage.

Validators enforce publishing constraints (non-empty labels, required URIs,
etc.) via PydanticCustomError for rich domain-specific error reporting.
Use model_construct() to bypass validation when building snapshots of
potentially-invalid projects (e.g. for preview).
"""

from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator
from pydantic_core import PydanticCustomError

from taxonomy_builder.models.concept import Concept
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.models.ontology_class import OntologyClass
from taxonomy_builder.models.project import Project
from taxonomy_builder.models.property import Property


class SnapshotConcept(BaseModel):
    """A concept within a snapshot scheme."""

    id: UUID
    pref_label: str
    identifier: str | None = None
    uri: str
    definition: str | None = None
    scope_note: str | None = None
    alt_labels: list[str] = Field(default_factory=list)
    broader_ids: list[UUID] = Field(default_factory=list)
    related_ids: list[UUID] = Field(default_factory=list)

    @field_validator("uri", mode="before")
    @classmethod
    def require_uri(cls, v: str | None, info: ValidationInfo) -> str:
        if v is None:
            label = info.data.get("pref_label", "?")
            raise PydanticCustomError(
                "concept_missing_uri",
                "Concept '{label}' has no URI.",
                {
                    "label": label,
                    "entity_type": "concept",
                    "entity_id": str(info.data.get("id", "")),
                    "entity_label": label,
                },
            )
        return v

    @field_validator("pref_label", mode="after")
    @classmethod
    def non_empty_label(cls, v: str, info: ValidationInfo) -> str:
        if not v.strip():
            raise PydanticCustomError(
                "concept_missing_pref_label",
                "A concept has an empty preferred label.",
                {
                    "entity_type": "concept",
                    "entity_id": str(info.data.get("id", "")),
                    "entity_label": v,
                },
            )
        return v

    @classmethod
    def from_concept(cls, concept: Concept) -> Self:
        """Generate a SnapshotConcept from a Concept"""
        return cls.model_construct(
            id=concept.id,
            identifier=concept.identifier,
            uri=concept.uri,
            pref_label=concept.pref_label,
            definition=concept.definition,
            scope_note=concept.scope_note,
            alt_labels=list(concept.alt_labels),
            broader_ids=[b.id for b in concept.broader],
            related_ids=[r.id for r in concept.related],
        )



class SnapshotScheme(BaseModel):
    """A concept scheme within a snapshot."""

    id: UUID
    title: str
    description: str | None = None
    uri: str
    concepts: list[SnapshotConcept] = Field(default_factory=list)

    @field_validator("uri", mode="before")
    @classmethod
    def require_uri(cls, v: str | None, info: ValidationInfo) -> str:
        if v is None:
            title = info.data.get("title", "?")
            raise PydanticCustomError(
                "scheme_missing_uri",
                "Scheme '{title}' has no URI.",
                {
                    "title": title,
                    "entity_type": "scheme",
                    "entity_id": str(info.data.get("id", "")),
                    "entity_label": title,
                },
            )
        return v

    @field_validator("concepts", mode="after")
    @classmethod
    def require_concepts(
        cls, v: list[SnapshotConcept], info: ValidationInfo
    ) -> list[SnapshotConcept]:
        if not v:
            title = info.data.get("title", "?")
            raise PydanticCustomError(
                "scheme_no_concepts",
                "Scheme '{title}' has no concepts.",
                {
                    "title": title,
                    "entity_type": "scheme",
                    "entity_id": str(info.data.get("id", "")),
                    "entity_label": title,
                },
            )
        return v

    @classmethod
    def from_scheme(cls, scheme: ConceptScheme) -> Self:
        return cls.model_construct(
            id=scheme.id,
            title=scheme.title,
            description=scheme.description,
            uri=scheme.uri,
            concepts=[SnapshotConcept.from_concept(c) for c in scheme.concepts],
        )


class SnapshotProperty(BaseModel):
    """A property within a snapshot."""

    id: UUID
    identifier: str
    label: str
    uri: str
    description: str | None = None
    domain_class: str
    range_scheme_id: UUID | None = None
    range_scheme_uri: str | None = None
    range_datatype: str | None = None
    range_class: str | None = None
    cardinality: str
    required: bool

    @field_validator("uri", mode="before")
    @classmethod
    def require_uri(cls, v: str | None, info: ValidationInfo) -> str:
        if v is None:
            label = info.data.get("label", "?")
            raise PydanticCustomError(
                "property_missing_uri",
                "Property '{label}' has no URI.",
                {
                    "label": label,
                    "entity_type": "property",
                    "entity_id": str(info.data.get("id", "")),
                    "entity_label": label,
                },
            )
        return v

    @model_validator(mode="after")
    def require_exactly_one_range(self) -> SnapshotProperty:
        has_scheme = self.range_scheme_id is not None
        has_datatype = self.range_datatype is not None
        has_class = self.range_class is not None
        if sum((has_scheme, has_datatype, has_class)) != 1:
            raise PydanticCustomError(
                "property_invalid_range",
                "Property '{label}' must have exactly one of"
                " range scheme, range datatype, or range class.",
                {
                    "label": self.label,
                    "entity_type": "property",
                    "entity_id": str(self.id),
                    "entity_label": self.label,
                },
            )
        if has_scheme and self.range_scheme_uri is None:
            raise PydanticCustomError(
                "property_missing_range_scheme_uri",
                "Property '{label}' has a range scheme ID but no range scheme URI.",
                {
                    "label": self.label,
                    "entity_type": "property",
                    "entity_id": str(self.id),
                    "entity_label": self.label,
                },
            )
        return self

    @classmethod
    def from_property(cls, property: Property) -> Self:
        return SnapshotProperty.model_construct(
            id=property.id,
            identifier=property.identifier,
            uri=property.uri,
            label=property.label,
            description=property.description,
            domain_class=property.domain_class,
            range_scheme_id=property.range_scheme_id,
            range_scheme_uri=property.range_scheme.uri if property.range_scheme else None,
            range_datatype=property.range_datatype,
            range_class=property.range_class,
            cardinality=property.cardinality,
            required=property.required,
        )


class SnapshotClass(BaseModel):
    """An ontology class within a snapshot."""

    id: UUID
    identifier: str
    label: str
    uri: str
    description: str | None = None
    scope_note: str | None = None

    @field_validator("label", mode="after")
    @classmethod
    def non_empty_label(cls, v: str, info: ValidationInfo) -> str:
        if not v.strip():
            raise PydanticCustomError(
                "class_missing_label",
                "A class has an empty label.",
                {
                    "entity_type": "class",
                    "entity_id": str(info.data.get("id", "")),
                    "entity_label": v,
                },
            )
        return v

    @field_validator("uri", mode="before")
    @classmethod
    def require_uri(cls, v: str | None, info: ValidationInfo) -> str:
        if v is None:
            label = info.data.get("label", "?")
            raise PydanticCustomError(
                "class_missing_uri",
                "Class '{label}' has no URI.",
                {
                    "label": label,
                    "entity_type": "class",
                    "entity_id": str(info.data.get("id", "")),
                    "entity_label": label,
                },
            )
        return v

    @classmethod
    def from_class(cls, ontology_class: OntologyClass) -> Self:
        return cls.model_construct(
            id=ontology_class.id,
            identifier=ontology_class.identifier,
            uri=ontology_class.uri,
            label=ontology_class.label,
            description=ontology_class.description,
            scope_note=ontology_class.scope_note,
        )


class SnapshotProjectMetadata(BaseModel):
    """Project metadata within a snapshot."""

    id: UUID
    name: str
    description: str | None = None
    namespace: str

    @field_validator("namespace", mode="before")
    @classmethod
    def require_namespace(cls, v: str | None, info: ValidationInfo) -> str:
        if v is None or not str(v).strip():
            raise PydanticCustomError(
                "project_missing_namespace",
                "Project has no namespace.",
                {
                    "entity_type": "project",
                    "entity_id": str(info.data.get("id", "")),
                    "entity_label": info.data.get("name", "?"),
                },
            )
        return v

    @classmethod
    def from_project(cls, project: Project) -> Self:
        return SnapshotProjectMetadata.model_construct(
            id=project.id,
            name=project.name,
            description=project.description,
            namespace=project.namespace,
        )


class SnapshotVocabulary(BaseModel):
    """Complete immutable snapshot of a project's vocabulary."""

    project: SnapshotProjectMetadata
    concept_schemes: list[SnapshotScheme] = Field(default_factory=list)
    properties: list[SnapshotProperty] = Field(default_factory=list)
    classes: list[SnapshotClass] = Field(default_factory=list)

    @field_validator("concept_schemes", mode="after")
    @classmethod
    def require_schemes(
        cls,
        v: list[SnapshotScheme],
    ) -> list[SnapshotScheme]:
        if not v:
            raise PydanticCustomError(
                "no_schemes",
                "Project has no concept schemes.",
                {},
            )
        return v

    @classmethod
    def from_project(cls, project: Project) -> Self:
        return cls.model_construct(
            project=SnapshotProjectMetadata.from_project(project),
            concept_schemes=[SnapshotScheme.from_scheme(s) for s in project.schemes],
            properties=[SnapshotProperty.from_property(p) for p in project.properties],
            classes=[SnapshotClass.from_class(c) for c in project.ontology_classes],
        )


class ValidationError(BaseModel):
    """A single validation error that blocks publishing."""

    code: str
    message: str
    entity_type: str | None = None
    entity_id: UUID | None = None
    entity_label: str | None = None


class ValidationResult(BaseModel):
    """Result of pre-publish validation."""

    valid: bool
    errors: list[ValidationError] = Field(default_factory=list)


class DiffItem(BaseModel):
    """A single changed entity in a diff."""

    id: UUID | None = None
    uri: str | None = None
    label: str
    entity_type: str


class FieldChange(BaseModel):
    """A single field change within a modified entity."""

    field: str
    old: str | None = None
    new: str | None = None


class ModifiedItem(BaseModel):
    """An entity that was modified between versions."""

    id: UUID
    label: str
    entity_type: str
    changes: list[FieldChange] = Field(default_factory=list)


class DiffResult(BaseModel):
    """Diff between current project state and last published version."""

    added: list[DiffItem] = Field(default_factory=list)
    modified: list[ModifiedItem] = Field(default_factory=list)
    removed: list[DiffItem] = Field(default_factory=list)
