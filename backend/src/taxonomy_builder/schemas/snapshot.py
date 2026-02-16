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
