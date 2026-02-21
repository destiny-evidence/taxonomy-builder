"""Pydantic schemas for immutable project snapshots.

These models define the contract for snapshot data stored in
PublishedVersion.snapshot (JSONB). Use SnapshotVocabulary.model_validate()
to deserialize from JSONB, and .model_dump() to serialize for storage.

Validators enforce publishing constraints (non-empty labels, required URIs,
etc.) via PydanticCustomError for rich domain-specific error reporting.
Use model_construct() to bypass validation when building snapshots of
potentially-invalid projects (e.g. for preview).
"""

from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator
from pydantic_core import PydanticCustomError


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


class SnapshotProperty(BaseModel):
    """A property within a snapshot."""

    id: UUID
    identifier: str
    uri: str
    label: str
    description: str | None = None
    domain_class: str
    range_scheme_id: UUID | None = None
    range_scheme_uri: str | None = None
    range_datatype: str | None = None
    cardinality: str
    required: bool

    @model_validator(mode="after")
    def require_exactly_one_range(self) -> SnapshotProperty:
        has_scheme = self.range_scheme_id is not None
        has_datatype = self.range_datatype is not None
        if has_scheme == has_datatype:
            raise PydanticCustomError(
                "property_invalid_range",
                "Property '{label}' must have either a range scheme"
                " or a range datatype, not both or neither.",
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
                "Property '{label}' has a range scheme ID"
                " but no range scheme URI.",
                {
                    "label": self.label,
                    "entity_type": "property",
                    "entity_id": str(self.id),
                    "entity_label": self.label,
                },
            )
        return self


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


class SnapshotProjectMetadata(BaseModel):
    """Project metadata within a snapshot."""

    id: UUID
    name: str
    description: str | None = None
    namespace: str | None = None


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
