# Published Document Format

Static JSON format served to the taxonomy reader frontend, projected from `PublishedVersion.snapshot`. Files are compressed to `.gz` at the blob level — compression is favourable due to repetitive JSON structure (keys, braces, quotes). UUIDv7 prefix similarity within a project gives a modest additional compression bonus.

## Storage layout

Versioning is at the project level. Each published version captures a complete snapshot of all schemes, concepts, ontology classes, and properties.

```text
/index.json                             # root: all projects + latest version pointers
/{project-id}/
  index.json                            # version picker for this project
  {version}/
    vocabulary.json                     # all schemes, concepts, classes, properties
```

The root index and project index are regenerated on every publish. Vocabulary files are immutable once written. Version strings (e.g. `1.0`, `2.0-pre1`) are used as directory names — safe per the version format constraint `^\d+(\.\d+)+(-pre\d+)?$`.

### Reader flow

1. `GET /index.json` — render project list. Each entry carries `latest_version` for a direct link.
2. User picks a project — `GET /{project-id}/{latest_version}/vocabulary.json` — render schemes, concepts, ontology. **Two fetches for the common case.**
3. User wants a different version — `GET /{project-id}/index.json` — show version picker — `GET /{project-id}/{version}/vocabulary.json`. **Third fetch only when switching versions.**

## File types

Three file types, each with a JSON Schema definition.

### Root index (`root-index.schema.json`)

Served at `/index.json`. Minimal entry point listing all published projects with their latest finalized version. This is the reader's landing page — no scheme or concept details, just enough to link to each project's latest vocabulary.

### Project index (`project-index.schema.json`)

Served at `/{project-id}/index.json`. Version picker for a single project. Lists all published versions (finalized and pre-release) ordered by semver descending, each with a content summary. Loaded on demand when the reader needs to browse or switch versions.

### Vocabulary file (`vocabulary.schema.json`)

Served at `/{project-id}/{version}/vocabulary.json`. Complete vocabulary data for one published version. Concepts are nested under their owning scheme; classes and properties are top-level. Cross-references use IDs and URIs.

**Schemes** own their concepts. Each scheme carries a flat concept map keyed by UUID (O(1) lookup) and a `top_concepts` array listing tree entry points. `narrower` is omitted because it is derivable from `broader`.

**Properties** are flat at the top level with `domain_class_uri` and `range_scheme_id` — they are a join between classes and schemes, so nesting under either side would privilege one navigation direction.

**Classes** carry their full metadata including `scope_note`.

## Considerations

### Pre-releases

Pre-releases (`2.0-pre1`, etc.) are included in the project index and have vocabulary files generated. The root index's `latest_version` only points to finalized versions.

### Caching

Vocabulary files are immutable (write-once) and can use aggressive cache headers (`Cache-Control: immutable`). The root and project index files are regenerated on each publish and should use shorter cache times or `must-revalidate`.

### Size estimates

Expected pattern: multiple schemes with moderate concept counts.

Per-entity byte estimates:

| Entity   | Bytes each |
| -------- | ---------- |
| Concept  | ~400       |
| Property | ~120       |
| Class    | ~150       |
| Scheme   | ~200       |

File-level estimates for a single vocabulary file:

| Scenario | Schemes | Concepts | Classes | Properties | Uncompressed | Gzipped |
| -------- | ------- | -------- | ------- | ---------- | ------------ | ------- |
| Small    | 3       | 50       | 5       | 10         | ~25 KB       | ~6 KB   |
| Typical  | 10      | 300      | 8       | 24         | ~130 KB      | ~30 KB  |
| Large    | 20      | 1000     | 12      | 40         | ~420 KB      | ~95 KB  |

Root index and project index are under 1 KB in all cases.
