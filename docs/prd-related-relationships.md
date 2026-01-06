# PRD: Related Relationships

## Overview

Extend the concept model to support associative "related" relationships between concepts, completing the core SKOS concept properties.

## Problem

Currently concepts only support hierarchical relationships (broader/narrower). SKOS vocabularies commonly include **related**: associative (non-hierarchical) relationships between concepts in the same scheme.

Without related relationships, exported taxonomies are incomplete and users cannot capture associative connections between concepts.

## Requirements

1. **Symmetric relationship** - if A is related to B, B is related to A
2. **Within same scheme only** - cannot relate concepts across schemes
3. **CRUD operations:**
   - Add related relationship between two concepts
   - Remove related relationship
4. **Display in UI:**
   - Show related concepts in concept detail panel
   - Click to navigate to related concept
5. **Prevent duplicates** - same pair cannot be related twice
6. **Prevent self-reference** - concept cannot be related to itself

## Data Model

```python
class ConceptRelated(Base):
    """Symmetric related relationship between concepts."""
    concept_id: Mapped[UUID]  # FK to Concept
    related_concept_id: Mapped[UUID]  # FK to Concept

    # Composite primary key ensures uniqueness
    # Store only one direction (concept_id < related_concept_id) to enforce symmetry
```

**Constraint:** Always store with `concept_id < related_concept_id` to avoid duplicates.

## API Changes

```
POST /api/concepts/{id}/related
{ "related_concept_id": "uuid" }

DELETE /api/concepts/{id}/related/{related_id}

GET /api/concepts/{id}
{
  "id": "...",
  "pref_label": "Dogs",
  "related": [
    { "id": "...", "pref_label": "Cats" },
    { "id": "...", "pref_label": "Veterinary Medicine" }
  ]
}
```

## UI Changes

### Concept Detail Panel

```
┌─────────────────────────────────┐
│ Dogs                            │
│                                 │
│ Definition: Domesticated...     │
│                                 │
│ Broader:                        │
│ • Mammals                       │
│                                 │
│ Related:                        │
│ • Cats                          │
│ • Veterinary Medicine           │
│ [+ Add Related]                 │
│                                 │
│ [Edit] [Delete]                 │
└─────────────────────────────────┘
```

## SKOS Export Updates

Update export to include:

```turtle
ex:dogs a skos:Concept ;
    skos:prefLabel "Dogs" ;
    skos:related ex:cats .
```

Note: Since related is symmetric, the export should include the relationship from both sides:

```turtle
ex:dogs skos:related ex:cats .
ex:cats skos:related ex:dogs .
```

## Out of Scope

- Related relationship types (all are generic `skos:related`)
- Cross-scheme relationships

## Success Criteria

- Can create/remove related relationships
- Related relationships are symmetric (shown on both concepts)
- Export includes related in valid SKOS
- Import (once built) handles related relationships
