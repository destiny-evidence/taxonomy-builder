"""Pydantic schemas for immutable project snapshots.

These models define the contract for snapshot data stored in
PublishedVersion.snapshot (JSONB). Use ProjectSnapshot.model_validate()
to deserialize from JSONB, and .model_dump() to serialize for storage.
"""

from pydantic import BaseModel


class SnapshotConcept(BaseModel):
    """A concept within a snapshot scheme."""

    id: str
    identifier: str | None
    uri: str | None
    pref_label: str
    definition: str | None
    scope_note: str | None
    alt_labels: list[str]
    broader_ids: list[str]
    related_ids: list[str]


class SnapshotScheme(BaseModel):
    """A concept scheme within a snapshot."""

    id: str
    title: str
    description: str | None
    uri: str | None
    concepts: list[SnapshotConcept]


class SnapshotProperty(BaseModel):
    """A property within a snapshot."""

    id: str
    identifier: str
    uri: str | None
    label: str
    description: str | None
    domain_class: str
    range_scheme_id: str | None
    range_scheme_uri: str | None
    range_datatype: str | None
    cardinality: str
    required: bool


class SnapshotClass(BaseModel):
    """An ontology class within a snapshot."""

    uri: str
    label: str
    description: str | None


class SnapshotProject(BaseModel):
    """Project metadata within a snapshot."""

    id: str
    name: str
    description: str | None
    namespace: str | None


class ProjectSnapshot(BaseModel):
    """Complete immutable snapshot of a project's vocabulary."""

    project: SnapshotProject
    concept_schemes: list[SnapshotScheme]
    properties: list[SnapshotProperty]
    classes: list[SnapshotClass]
