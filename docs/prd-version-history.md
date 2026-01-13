# PRD: Version History & Published Versions

## Overview

Track all changes to concept schemes and concepts with full audit history. Enable users to view what changed, when, and by whom. Support publishing immutable numbered versions of schemes.

## Problem

Taxonomies evolve over time. Without version history:

- Users cannot see who made changes or why
- There's no audit trail for compliance
- Collaboration is difficult without change visibility
- No way to publish stable, referenceable versions

## Scope

### MVP

- Change tracking for all mutations (audit log)
- History viewing (scheme-level and concept-level)
- Published versions (immutable snapshots, exportable)

### Deferred

- Revert functionality
- Version comparison/diffing
- Branching/merging
- Change comments/commit messages
- User display names (until auth exists)

## Requirements

### Change Tracking

1. **Track all mutations:**
   - Create, update, delete for: ConceptSchemes, Concepts
   - Relationship changes: broader added/removed, related added/removed
2. **Capture for each change:**
   - Timestamp (when)
   - User ID (who) - placeholder until auth exists
   - Entity type and ID (what)
   - Action type (create, update, delete)
   - Before/after values (for updates)
3. **Automatic** - no user action required to track changes
4. **Explicit relationship events** - when deleting a concept, record separate delete events for each relationship before the concept delete

### History Viewing

1. **Scheme history:** View all changes within a scheme (including its concepts)
2. **Concept history:** View changes to a specific concept
3. **Timeline view:** Chronological list of changes
4. **Change detail:** Show exactly what changed (diff view)

### Published Versions

1. **Publish a version:** Create an immutable snapshot of a scheme at a point in time
2. **Version labels:** Semantic versioning (e.g., "1.0", "2.0")
3. **List versions:** View all published versions for a scheme
4. **Export versions:** Download a published version as SKOS (Turtle, RDF/XML, JSON-LD)
5. **Version metadata:** Published timestamp, optional notes

## Data Model

### ChangeEvent (Audit Log)

Store each change as an immutable event:

```python
class ChangeEvent(Base):
    """Immutable log of all changes."""
    __tablename__ = "change_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    timestamp: Mapped[datetime] = mapped_column(default=func.now())
    user_id: Mapped[UUID | None]  # Nullable until auth exists

    # What changed
    entity_type: Mapped[str]  # "concept", "concept_scheme", "concept_broader", "concept_related"
    entity_id: Mapped[UUID]
    scheme_id: Mapped[UUID]  # FK to concept_schemes, for filtering

    # Type of change
    action: Mapped[str]  # "create", "update", "delete", "publish"

    # State
    before_state: Mapped[dict | None] = mapped_column(JSONB)  # null for create
    after_state: Mapped[dict | None] = mapped_column(JSONB)   # null for delete
```

**Indexes:**

- `(scheme_id, timestamp DESC)` - scheme history
- `(entity_type, entity_id, timestamp DESC)` - entity history

### PublishedVersion (Immutable Snapshots)

```python
class PublishedVersion(Base):
    """Immutable snapshot of a scheme at a point in time."""
    __tablename__ = "published_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    scheme_id: Mapped[UUID] = mapped_column(ForeignKey("concept_schemes.id"))
    version_label: Mapped[str]  # "1.0", "2.0", etc.
    published_at: Mapped[datetime] = mapped_column(default=func.now())
    notes: Mapped[str | None]

    # Full snapshot of scheme state
    snapshot: Mapped[dict] = mapped_column(JSONB)
```

**Snapshot format:**

```json
{
  "scheme": {
    "id": "uuid",
    "title": "Animals",
    "description": "...",
    "uri": "http://example.org/animals"
  },
  "concepts": [
    {
      "id": "uuid",
      "pref_label": "Dogs",
      "identifier": "dogs",
      "definition": "...",
      "scope_note": "...",
      "alt_labels": ["Canines"],
      "broader_ids": ["uuid-of-mammals"],
      "related_ids": ["uuid-of-cats"]
    }
  ]
}
```

**Constraints:**

- Unique constraint on `(scheme_id, version_label)`

## API Endpoints

### Scheme History

```http
GET /api/schemes/{id}/history?limit=50&offset=0

Response:
{
  "events": [
    {
      "id": "uuid",
      "timestamp": "2024-01-15T10:30:00Z",
      "user_id": null,
      "entity_type": "concept",
      "entity_id": "uuid",
      "action": "update",
      "before_state": { "pref_label": "Dog", "definition": null },
      "after_state": { "pref_label": "Dogs", "definition": "..." }
    }
  ],
  "total": 150
}
```

### Concept History

```http
GET /api/concepts/{id}/history

Response:
{
  "events": [
    {
      "id": "uuid",
      "timestamp": "2024-01-15T10:30:00Z",
      "action": "update",
      "before_state": { "pref_label": "Dog", "definition": null },
      "after_state": { "pref_label": "Dogs", "definition": "..." }
    }
  ]
}
```

### Published Versions API

```http
POST /api/schemes/{id}/versions
{ "version_label": "1.0", "notes": "Initial release" }

Response:
{ "id": "uuid", "version_label": "1.0", "published_at": "2024-01-15T10:30:00Z" }
```

```http
GET /api/schemes/{id}/versions

Response:
{
  "versions": [
    { "id": "uuid", "version_label": "1.0", "published_at": "2024-01-15T10:30:00Z", "notes": "..." }
  ]
}
```

```http
GET /api/versions/{id}

Response:
{
  "id": "uuid",
  "version_label": "1.0",
  "published_at": "2024-01-15T10:30:00Z",
  "notes": "...",
  "snapshot": { ... }
}
```

```http
GET /api/versions/{id}/export?format=ttl

Response: SKOS Turtle file
```

## UI Components

### History Panel (Scheme Detail Page)

Add "History" tab or sidebar section:

```
┌─────────────────────────────────┐
│ History                    [↻]  │
├─────────────────────────────────┤
│ Today                           │
│ ├─ 10:30 Updated "Dogs"         │
│ │   definition changed          │
│ ├─ 10:15 Created "Cats"         │
│                                 │
│ Yesterday                       │
│ ├─ 15:00 Deleted "Fish"         │
│ ├─ 14:30 Added broader: Dogs →  │
│ │   Mammals                     │
└─────────────────────────────────┘
```

### Versions Panel

```text
┌─────────────────────────────────┐
│ Published Versions   [Publish]  │
├─────────────────────────────────┤
│ v2.0 - Jan 20, 2024             │
│   Added mammals category        │
│   [Export ▾]                    │
│                                 │
│ v1.0 - Jan 15, 2024             │
│   Initial release               │
│   [Export ▾]                    │
└─────────────────────────────────┘
```

## Migration

- Add `change_events` table with indexes
- Add `published_versions` table
- No backfill needed - history starts from deployment
- Existing data has no history (acceptable for MVP)

## Success Criteria

- All CRUD operations automatically create change events
- Relationship deletions are tracked as separate events
- Users can view chronological history for a scheme
- Users can view detailed history for a concept
- Users can see before/after state for updates
- Users can publish numbered versions of a scheme
- Users can export published versions as SKOS
