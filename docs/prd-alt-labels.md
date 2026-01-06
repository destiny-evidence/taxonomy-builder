# PRD: Alt Labels

## Overview

Extend the concept model to support alternative labels (synonyms, abbreviations), a core SKOS concept property.

## Problem

Currently concepts only have a single `pref_label`. SKOS vocabularies commonly include **altLabel**: synonyms, abbreviations, and spelling variants that help users find concepts.

Without alt labels, exported taxonomies are incomplete and users cannot capture the full richness of their vocabularies.

## Requirements

1. **Multiple altLabels per concept** - stored as a list
2. **CRUD operations:**
   - Add altLabel to concept
   - Remove altLabel from concept
   - Edit existing altLabel
3. **Display in UI:**
   - Show altLabels in concept detail panel
   - Inline editing (add/remove chips)
4. **Search inclusion** (future): altLabels should be searchable

## Data Model

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

## API Changes

Extend existing concept endpoints:

```
PUT /api/concepts/{id}
{
  "pref_label": "Dogs",
  "alt_labels": ["Canines", "Domestic dogs", "Canis familiaris"]
}
```

Alt labels are included in concept responses:

```
GET /api/concepts/{id}
{
  "id": "...",
  "pref_label": "Dogs",
  "alt_labels": ["Canines", "Domestic dogs", "Canis familiaris"],
  ...
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
    skos:altLabel "Domestic dogs" .
```

## Out of Scope

- Hidden labels (`skos:hiddenLabel`)
- Language tags on labels

## Success Criteria

- Can add/remove multiple altLabels on a concept
- Export includes altLabels in valid SKOS
- Import (once built) handles altLabels
