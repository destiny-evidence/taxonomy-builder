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
   - Scheme title and description
   - Number of concepts found
   - Number of relationships found
   - Any validation warnings
6. User clicks "Import" to confirm
7. System creates scheme and concepts
8. User is redirected to the new scheme

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
  "scheme": {
    "title": "My Taxonomy",
    "description": "...",
    "uri": "http://example.org/taxonomy"
  },
  "concepts_count": 42,
  "relationships_count": 38,
  "warnings": ["Concept http://... has no prefLabel, using URI fragment"]
}
```

**Response (dry_run=false):**
```json
{
  "scheme_id": "uuid",
  "concepts_created": 42,
  "relationships_created": 38
}
```

**Implementation:**

```python
from rdflib import Graph
from rdflib.namespace import SKOS, RDF, DCTERMS

def parse_skos(file_content: bytes, format: str) -> ImportPreview:
    g = Graph()
    g.parse(data=file_content, format=format)

    # Find ConceptScheme
    schemes = list(g.subjects(RDF.type, SKOS.ConceptScheme))

    # Find all Concepts
    concepts = list(g.subjects(RDF.type, SKOS.Concept))

    # Extract properties and relationships
    # ...
```

### Frontend

- Add "Import Scheme" button to `ProjectDetailPage`
- File input component (drag-and-drop optional, stretch goal)
- Preview modal showing import summary
- Progress indicator during import
- Error display for validation failures

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Multiple ConceptSchemes in file | Error: "File contains multiple schemes. Please import one at a time." |
| No ConceptScheme found | Create implicit scheme from concepts |
| Concept without prefLabel | Warning, use URI local name as label |
| Circular broader relationships | Warning, import anyway (valid SKOS DAG) |
| Duplicate URIs | Error: "Concept with URI X already exists" |
| Unsupported RDF format | Error: "Could not parse file. Supported formats: RDF/XML, Turtle, JSON-LD, N-Triples" |

## Out of Scope

- Import multiple schemes at once
- Merge into existing scheme
- Conflict resolution for updates
- Import from URL (only file upload)
- altLabel import (defer until altLabel feature exists)
- related relationships (defer until related feature exists)

## Success Criteria

- Successfully import standard SKOS files from:
  - SKOS Play exports
  - PoolParty exports
  - Hand-crafted Turtle files
- Round-trip: export then import produces equivalent data
- Import of 500-concept file completes in <30 seconds
- Validation catches common SKOS errors with helpful messages
