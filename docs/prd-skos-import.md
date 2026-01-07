# PRD: SKOS Import

## Overview

Enable users to import existing SKOS vocabularies from RDF files, allowing migration of taxonomies from other systems into the application.

## Problem

Organizations often have existing taxonomies in SKOS format from other tools or standards bodies. Without import capability, users must manually recreate these structures, which is time-consuming and error-prone.

## Requirements

### Functional

1. **Import SKOS RDF files** into an existing project
2. **Support multiple serialization formats:**
   - RDF/XML (`.rdf`)
   - Turtle (`.ttl`)
   - JSON-LD (`.jsonld`)
   - N-Triples (`.nt`)
3. **Parse and create:**
   - `skos:ConceptScheme` → ConceptScheme record
   - `skos:Concept` → Concept records
   - `skos:broader` → ConceptBroader relationships
   - Extract prefLabel, definition, scopeNote, altLabel (if present)
4. **Handle URI mapping:**
   - Preserve original concept URIs where possible
   - Extract identifiers from URIs for local storage
5. **Validate before import:**
   - Check for valid SKOS structure
   - Report errors/warnings before committing
6. **Preview before commit:**
   - Show what will be created (X concepts, Y relationships)
   - Allow user to cancel or proceed

### Non-Functional

- Import completes within 30 seconds for files with 500+ concepts
- Clear error messages for malformed RDF or invalid SKOS

## User Flow

1. User navigates to a project
2. User clicks "Import Scheme" button
3. File picker opens, user selects RDF file
4. System parses and validates the file
5. Preview modal shows:
   - Each scheme as an individual card with:
     - Scheme title and description
     - Number of concepts found
     - Number of relationships found
     - Any validation warnings for that scheme
   - Total counts across all schemes
6. User clicks "Import" to confirm (imports all schemes)
7. System creates all schemes and concepts atomically
8. User is redirected to the project (showing newly imported schemes)

## Technical Approach

### Backend

**New endpoint:** `POST /api/projects/{id}/import`

- Accept multipart file upload
- Parse RDF using RDFLib
- Validate SKOS structure
- Return preview (dry-run) or commit

**Request:**
```
POST /api/projects/{id}/import
Content-Type: multipart/form-data

file: <rdf-file>
dry_run: true|false (default: true)
```

**Response (dry_run=true):**

```json
{
  "valid": true,
  "schemes": [
    {
      "title": "Taxonomy A",
      "description": "...",
      "uri": "http://example.org/taxonomy-a",
      "concepts_count": 42,
      "relationships_count": 38,
      "warnings": []
    },
    {
      "title": "Taxonomy B",
      "description": "...",
      "uri": "http://example.org/taxonomy-b",
      "concepts_count": 15,
      "relationships_count": 12,
      "warnings": ["Concept http://... has no prefLabel, using URI fragment"]
    }
  ],
  "total_concepts_count": 57,
  "total_relationships_count": 50
}
```

**Response (dry_run=false):**

```json
{
  "schemes_created": [
    {"id": "uuid-1", "title": "Taxonomy A", "concepts_created": 42},
    {"id": "uuid-2", "title": "Taxonomy B", "concepts_created": 15}
  ],
  "total_concepts_created": 57,
  "total_relationships_created": 50
}
```

**Implementation:**

```python
from rdflib import Graph, RDF, RDFS
from rdflib.namespace import SKOS, DCTERMS

def parse_skos(file_content: bytes, format: str) -> ImportPreview:
    g = Graph()
    g.parse(data=file_content, format=format)

    # Find all ConceptSchemes
    schemes = list(g.subjects(RDF.type, SKOS.ConceptScheme))

    # Find all Concepts (including subclass instances)
    concepts = set()
    for concept_class in g.transitive_subjects(RDFS.subClassOf, SKOS.Concept):
        for instance in g.subjects(RDF.type, concept_class):
            concepts.add(instance)
    for instance in g.subjects(RDF.type, SKOS.Concept):
        concepts.add(instance)

    # Group concepts by scheme (via skos:inScheme or skos:topConceptOf)
    # Extract properties and relationships per scheme
    # ...
```

**Scheme title extraction priority:**

1. `rdfs:label`
2. `skos:prefLabel`
3. `dcterms:title`
4. URI local name (fallback)

**Concept properties to extract:**

| SKOS Property | Model Field | Notes |
|---------------|-------------|-------|
| `skos:prefLabel` | `pref_label` | Required (warn if missing, use URI local name) |
| `skos:definition` | `definition` | Optional |
| `skos:scopeNote` | `scope_note` | Optional |
| `skos:altLabel` | `alt_labels` | Optional, multiple allowed |
| `skos:broader` | broader relationship | Via ConceptBroader join table |
| `skos:narrower` | (inferred) | Don't duplicate - derive from broader |

### Frontend

- Add "Import Scheme" button to `ProjectDetailPage`
- File input component (drag-and-drop optional, stretch goal)
- Preview modal showing import summary
- Progress indicator during import
- Error display for validation failures

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Multiple ConceptSchemes in file | Supported - import all schemes, shown as individual cards in preview |
| Scheme URI already exists in project | Error: "A scheme with URI X already exists in this project" |
| Scheme title already exists in project | Auto-rename: append " (2)", " (3)", etc. |
| No ConceptScheme found | Create implicit scheme from concepts |
| Concept without prefLabel | Warning, use URI local name as label |
| Concept without scheme membership | If single scheme in file: assign to it. If multiple schemes: warning, skip concept |
| Circular broader relationships | Warning, import anyway (valid SKOS DAG) |
| Duplicate concept URIs | Error: "Concept with URI X already exists" |
| Unsupported RDF format | Error: "Could not parse file. Supported formats: RDF/XML, Turtle, JSON-LD, N-Triples" |

## Out of Scope

- Selective import of individual schemes from multi-scheme file (all-or-nothing for now)
- Merge into existing scheme
- Conflict resolution for updates
- Import from URL (only file upload)
- `skos:notation` import (requires model change)
- `skos:exactMatch` and other mapping relations

## Success Criteria

- Successfully import standard SKOS files from:
  - SKOS Play exports
  - PoolParty exports
  - Hand-crafted Turtle files
- Round-trip: export then import produces equivalent data
- Import of 500-concept file completes in <30 seconds
- Validation catches common SKOS errors with helpful messages
