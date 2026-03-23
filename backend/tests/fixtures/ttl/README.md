# TTL Test Fixtures

Turtle files for import testing — both automated and manual. Each file is a
self-contained vocabulary that can be imported into a taxonomy builder project
via the `/api/projects/{id}/import` endpoint or the UI import dialog.

## Files

### ontology-expressivity.ttl

Exercises the full range of OWL/RDFS features supported by the import pipeline:

- **Class hierarchy**: 3 levels deep (Entity → Study → RCT), two branches
- **Diamond inheritance**: MeasuredOutcome is a subclass of both Outcome and Finding
- **Multi-domain properties**: `owl:unionOf` domains spanning multiple classes
- **Property types**: `owl:ObjectProperty`, `owl:DatatypeProperty`, `rdf:Property`
- **OWL restrictions**: `allValuesFrom`, `someValuesFrom`, `hasValue`
- **Equal-depth tie-breaking**: multi-domain property on two parents at the same
  depth in a diamond — tests alphabetical grouping in the closure UI
- **Concept schemes**: two schemes with hierarchical concepts, used as range targets
- **Concept-typed classes**: `rdfs:subClassOf skos:Concept` for scheme-backed ranges

Import into a fresh project with namespace `https://example.org/epic108/`.
The file header documents expected UI behaviour per class after import.

## Adding fixtures

When adding a new TTL file, please:

1. Add a section to this README describing what the file exercises
2. Include comments in the TTL file explaining the expected import behaviour
3. Use the `https://example.org/` namespace (or a sub-path of it)
