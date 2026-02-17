"""Pydantic schemas for immutable project snapshots.

These models define the contract for snapshot data stored in
PublishedVersion.snapshot (JSONB). Use VocabularySnapshot.model_validate()
to deserialize from JSONB, and .model_dump() to serialize for storage.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class SnapshotConcept(BaseModel):
    """A concept within a snapshot scheme."""

    id: UUID
    identifier: str | None = None
    uri: str | None = None
    pref_label: str
    definition: str | None = None
    scope_note: str | None = None
    alt_labels: list[str] = Field(default_factory=list)
    broader_ids: list[UUID] = Field(default_factory=list)
    related_ids: list[UUID] = Field(default_factory=list)


class SnapshotScheme(BaseModel):
    """A concept scheme within a snapshot."""

    id: UUID
    title: str
    description: str | None = None
    uri: str | None = None
    concepts: list[SnapshotConcept] = Field(default_factory=list)


class SnapshotProperty(BaseModel):
    """A property within a snapshot."""

    id: UUID
    identifier: str
    uri: str | None = None
    label: str
    description: str | None = None
    domain_class: str
    range_scheme_id: UUID | None = None
    range_scheme_uri: str | None = None
    range_datatype: str | None = None
    cardinality: str
    required: bool


class SnapshotClass(BaseModel):
    """An ontology class within a snapshot."""

    uri: str
    label: str
    description: str | None = None


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

    id: UUID
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
