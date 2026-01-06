# PRD: Alt Labels & Related Relationships

## Overview

Extend the concept model to support alternative labels (synonyms, abbreviations) and associative "related" relationships between concepts, completing the core SKOS concept properties.

## Problem

Currently concepts only have a single `pref_label`. SKOS vocabularies commonly include:
- **altLabel**: synonyms, abbreviations, spelling variants that help users find concepts
- **related**: associative (non-hierarchical) relationships between concepts in the same scheme

Without these, exported taxonomies are incomplete and users cannot capture the full richness of their vocabularies.

## Requirements

### Alt Labels

1. **Multiple altLabels per concept** - stored as a list
2. **CRUD operations:**
   - Add altLabel to concept
   - Remove altLabel from concept
   - Edit existing altLabel
3. **Display in UI:**
   - Show altLabels in concept detail panel
   - Inline editing (add/remove chips)
4. **Search inclusion** (future): altLabels should be searchable

### Related Relationships

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

### Alt Labels

**Option A: JSON array column**
```python
class Concept(Base):
    alt_labels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
```

**Option B: Separate table** (better for search indexing)
```python
class ConceptAltLabel(Base):
    id: Mapped[UUID]
    concept_id: Mapped[UUID]  # FK to Concept
    label: Mapped[str]
```

Recommend **Option A** for simplicity. Alt labels are always fetched with the concept and don't need independent querying in MVP.

### Related Relationships

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

### Alt Labels

Extend existing concept endpoints:

```
PUT /api/concepts/{id}
{
  "pref_label": "Dogs",
  "alt_labels": ["Canines", "Domestic dogs", "Canis familiaris"]
}
```

### Related Relationships

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
│ Alt Labels:                     │
│ [Canines ×] [Domestic dogs ×]   │
│ [+ Add]                         │
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

### Concept Form

Add alt labels input:
- Text input with "Add" button
- Display as removable chips
- Allow editing inline

## SKOS Export Updates

Update export to include:

```turtle
ex:dogs a skos:Concept ;
    skos:prefLabel "Dogs" ;
    skos:altLabel "Canines" ;
    skos:altLabel "Domestic dogs" ;
    skos:related ex:cats .
```

## Out of Scope

- Hidden labels (`skos:hiddenLabel`)
- Language tags on labels
- Related relationship types (all are generic `skos:related`)

## Success Criteria

- Can add/remove multiple altLabels on a concept
- Can create/remove related relationships
- Related relationships are symmetric (shown on both concepts)
- Export includes altLabels and related in valid SKOS
- Import (once built) handles altLabels and related
