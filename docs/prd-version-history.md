# PRD: Version History

## Overview

Track all changes to concept schemes and concepts with full audit history, enabling users to view what changed, when, and by whom, with the ability to revert to previous versions.

## Problem

Taxonomies evolve over time. Without version history:
- Users cannot see who made changes or why
- Accidental changes cannot be undone
- There's no audit trail for compliance
- Collaboration is difficult without change visibility

## Requirements

### Change Tracking

1. **Track all mutations:**
   - Create, update, delete for: Projects, ConceptSchemes, Concepts
   - Relationship changes: broader added/removed, related added/removed
2. **Capture for each change:**
   - Timestamp (when)
   - User ID (who) - placeholder until auth exists
   - Entity type and ID (what)
   - Action type (create, update, delete)
   - Before/after values (for updates)
3. **Automatic** - no user action required to track changes

### History Viewing

1. **Scheme history:** View all changes within a scheme (including its concepts)
2. **Concept history:** View changes to a specific concept
3. **Timeline view:** Chronological list of changes
4. **Change detail:** Show exactly what changed (diff view)

### Version Comparison

1. **Side-by-side diff** for concept changes
2. **Highlight additions, removals, modifications**

### Revert

1. **Revert a concept** to a previous state
2. **Confirmation required** before revert
3. **Revert creates a new change** (not destructive)

## Data Model

### Approach: Event Log

Store each change as an immutable event:

```python
class ChangeEvent(Base):
    """Immutable log of all changes."""
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    timestamp: Mapped[datetime] = mapped_column(default=func.now())
    user_id: Mapped[UUID | None]  # Nullable until auth exists

    # What changed
    entity_type: Mapped[str]  # "concept", "concept_scheme", "project"
    entity_id: Mapped[UUID]
    scheme_id: Mapped[UUID | None]  # For filtering by scheme

    # Type of change
    action: Mapped[str]  # "create", "update", "delete"

    # State
    before_state: Mapped[dict | None] = mapped_column(JSON)  # null for create
    after_state: Mapped[dict | None] = mapped_column(JSON)   # null for delete
```

**Why event log over snapshots:**
- Storage efficient (only store changes)
- Natural audit trail
- Can reconstruct any point in time
- Simpler than managing snapshot versions

### Indexes

- `(scheme_id, timestamp DESC)` - scheme history
- `(entity_type, entity_id, timestamp DESC)` - entity history

## API Endpoints

### Scheme History

```
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
      "entity_label": "Dogs",
      "action": "update",
      "changes": {
        "definition": {
          "before": "A domestic animal",
          "after": "A domesticated carnivorous mammal"
        }
      }
    }
  ],
  "total": 150
}
```

### Concept History

```
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
    },
    {
      "id": "uuid",
      "timestamp": "2024-01-14T09:00:00Z",
      "action": "create",
      "before_state": null,
      "after_state": { "pref_label": "Dog" }
    }
  ]
}
```

### Revert

```
POST /api/concepts/{id}/revert
{ "to_event_id": "uuid" }

Response:
{ "success": true, "new_event_id": "uuid" }
```

## Implementation

### Recording Changes

Create a service decorator or middleware:

```python
async def record_change(
    session: AsyncSession,
    entity_type: str,
    entity_id: UUID,
    action: str,
    before: dict | None,
    after: dict | None,
    scheme_id: UUID | None = None,
    user_id: UUID | None = None,
):
    event = ChangeEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_state=before,
        after_state=after,
        scheme_id=scheme_id,
        user_id=user_id,
    )
    session.add(event)
```

Integrate into existing service methods:

```python
async def update_concept(self, concept_id: UUID, data: ConceptUpdate) -> Concept:
    concept = await self.get(concept_id)
    before = concept_to_dict(concept)

    # Apply updates...

    after = concept_to_dict(concept)
    await record_change(self.session, "concept", concept_id, "update", before, after, concept.scheme_id)

    return concept
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

### Concept History Modal

Show full history for a concept with diff view:

```
┌─────────────────────────────────────────────┐
│ History: Dogs                          [×]  │
├─────────────────────────────────────────────┤
│ Jan 15, 10:30 - Updated                     │
│ ┌─────────────────┬─────────────────┐       │
│ │ Before          │ After           │       │
│ ├─────────────────┼─────────────────┤       │
│ │ definition:     │ definition:     │       │
│ │ A domestic      │ A domesticated  │       │
│ │ animal          │ carnivorous     │       │
│ │                 │ mammal          │       │
│ └─────────────────┴─────────────────┘       │
│                          [Revert to this]   │
├─────────────────────────────────────────────┤
│ Jan 14, 09:00 - Created                     │
│ Initial creation                            │
└─────────────────────────────────────────────┘
```

## Out of Scope

- Named versions/tags ("v1.0", "v2.0")
- Branching/merging
- Bulk revert (revert entire scheme)
- Change comments/commit messages
- User display names (until auth exists)

## Migration

- Add `change_events` table
- No backfill needed - history starts from deployment
- Existing data has no history (acceptable for MVP)

## Success Criteria

- All CRUD operations automatically create change events
- Users can view chronological history for a scheme
- Users can view detailed history for a concept
- Users can see before/after diff for updates
- Users can revert a concept to a previous state
- Revert creates a new change event (audit trail preserved)
