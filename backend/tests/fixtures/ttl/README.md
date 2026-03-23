# TTL Test Fixtures

Turtle files for import testing — both automated and manual. Each file is a
self-contained vocabulary that can be imported into a taxonomy builder project
via the `/api/projects/{id}/import` endpoint or the UI import dialog.

## Files

### ontology-expressivity.ttl

Exercises the full range of OWL/RDFS features supported by the import pipeline
(class hierarchy, diamond inheritance, multi-domain properties, property types,
OWL restrictions, concept schemes, concept-typed classes). See the file header
comment for the complete list of features and expected UI behaviour per class.

Import into a fresh project with namespace `https://example.org/epic108/`.

## Adding fixtures

When adding a new TTL file, please:

1. Add a section to this README describing what the file exercises
2. Include comments in the TTL file explaining the expected import behaviour
3. Use the `https://example.org/` namespace (or a sub-path of it)
