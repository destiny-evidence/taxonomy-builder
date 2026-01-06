# PRD: SKOS Export

## Overview

Enable users to export concept schemes as SKOS-compliant RDF files for integration with external systems and evidence platforms.

## Problem

Users can create and manage taxonomies in the application, but cannot yet export them in standard formats for use in other systems. The evidence platform requires SKOS RDF files to configure tagging and classification features.

## Requirements

### Functional

1. **Export a single concept scheme** to SKOS RDF format
2. **Support multiple serialization formats:**
   - RDF/XML (`.rdf`) - widest compatibility
   - Turtle (`.ttl`) - human-readable
   - JSON-LD (`.jsonld`) - web-friendly
3. **Include all SKOS properties:**
   - `skos:ConceptScheme` with title, description, publisher, version
   - `skos:Concept` with prefLabel, definition, scopeNote
   - `skos:broader` / `skos:narrower` relationships
   - `skos:inScheme` linking concepts to their scheme
4. **Generate valid URIs:**
   - Use scheme's `uri` field as base (or generate default)
   - Concept URIs derived from `scheme.uri + concept.identifier`
5. **Validate output** against SKOS constraints before download

### Non-Functional

- Export completes within 5 seconds for schemes with 500+ concepts
- Generated RDF passes validation with external SKOS validators

## User Flow

### Scheme Export

1. User navigates to a concept scheme
2. User clicks "Export" button in scheme header
3. Modal appears with format selection (RDF/XML, Turtle, JSON-LD)
4. User selects format and clicks "Download"
5. Browser downloads the file (e.g., `my-taxonomy.ttl`)

## Technical Approach

### Backend

**New endpoint:** `GET /api/schemes/{id}/export?format={rdf|ttl|jsonld}`

**Implementation using RDFLib:**

```python
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import SKOS, RDF, DCTERMS

def export_scheme(scheme: ConceptScheme, concepts: list[Concept], format: str) -> str:
    g = Graph()
    g.bind("skos", SKOS)
    g.bind("dct", DCTERMS)

    scheme_uri = URIRef(scheme.uri or f"http://example.org/schemes/{scheme.id}")
    g.add((scheme_uri, RDF.type, SKOS.ConceptScheme))
    g.add((scheme_uri, DCTERMS.title, Literal(scheme.title)))
    # ... add concepts, relationships

    return g.serialize(format=format)
```

**Response:** Return file with appropriate `Content-Type` and `Content-Disposition` headers.

### Frontend

- Add "Export" button to `SchemeDetailPage` header
- Simple modal with format dropdown and download button
- Use `<a download>` or `window.open()` to trigger browser download

## SKOS Mapping

| App Field | SKOS Property |
|-----------|---------------|
| ConceptScheme.title | `dct:title` |
| ConceptScheme.description | `dct:description` |
| ConceptScheme.publisher | `dct:publisher` |
| ConceptScheme.version | `owl:versionInfo` |
| Concept.pref_label | `skos:prefLabel` |
| Concept.definition | `skos:definition` |
| Concept.scope_note | `skos:scopeNote` |
| Concept.uri | Concept URI |
| broader relationship | `skos:broader` / `skos:narrower` |

## Out of Scope

- Batch export of multiple schemes
- Export history/versioning
- altLabel export (not yet implemented in app)
- related relationships (not yet implemented in app)

## Success Criteria

- Exported files validate with [SKOS Testing Tool](https://skos-play.sparna.fr/play/validate)
- Round-trip: export then import produces equivalent data (once import exists)
- Export of 500-concept scheme completes in <5 seconds
