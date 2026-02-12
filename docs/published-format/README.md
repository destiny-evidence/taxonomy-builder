# Published Document Format

Static JSON format served to the taxonomy reader frontend, projected from `PublishedVersion.snapshot`. These are compressed to `.gz` at the blob level - this compression factor should be quite favourable as the majority of the data are `UUIDv7`s which have similar prefixes.

## Storage layout

Each scheme is versioned independently.

```none
/{project-id}/
  index.json                  # project metadata + list of schemes
  ontology.json               # domain classes + properties
  {scheme-id}/
    index.json                # scheme metadata + version list
    {version-id}.json         # concept data for a specific version
```

The project index and ontology file are regenerated whenever any scheme publishes a new version. Version files are immutable once published. Filenames use version UUIDs rather than user-provided version labels, avoiding filename-safety concerns. The project index carries `latest_path` per scheme, giving the reader a direct relative path to the latest vocabulary file.

### Reader flow

1. Fetch `/{project-id}/index.json` — render scheme list. Each scheme includes `latest_path`
2. User picks a vocabulary — fetch `/{project-id}/{latest_path}` — render concepts
3. User wants a different version — fetch `/{project-id}/{scheme-id}/index.json` — show version picker — fetch `/{project-id}/{scheme-id}/{path}`
4. User wants domain models & properties — fetch `/{project-id}/ontology.json`. Reader can use index loaded from 1. to navigate to vocabularies from here.

## File types

Four file types, each with a JSON Schema definition:

### Project index (`project-index.schema.json`)

Served at `/{project-id}/index.json`. Contains current project metadata and a list of published schemes with their latest version label, path to the latest vocabulary file, and concept count - only the information required for navigation from a landing page. This is the reader's entry point.

### Vocabulary index (`vocabulary-index.schema.json`)

Served at `/{project-id}/{scheme-id}/index.json`. Lists available versions of a scheme/vocabulary with release notes and timestamps. Only loaded on demand when the reader needs to view/switch versions.

### Ontology file (`ontology.schema.json`)

Served at `/{project-id}/ontology.json`. Contains the domain classes from the core ontology and the properties that link them to concept schemes or datatypes. Properties reference schemes by UUID (cross-reference with the project index's `schemes` array) and domain classes by URI (resolve labels from the `domain_classes` array in the same file). Loaded on demand when the reader needs to display the domain model.

As a first pass this is updated whenever a property is updated. We should consider a publishing mechanism.

### Vocabulary file (`vocabulary.schema.json`)

Served at `/{project-id}/{scheme-id}/{version-id}.json`. Contains the scheme ID and all concepts as a flat map keyed by UUID. Each concept carries `pref_label`, `definition`, `scope_note`, `alt_labels` (for search), `broader` (parent IDs), and `related` (related concept IDs). A `top_concepts` array lists root entry points for tree rendering. Scheme metadata is taken from the higher index file.

This is normalized, meaning each concept's information is only represented once, but does require the client to build the tree in `O(n)` time.

## Considerations

### Future implications

Issue [#33](https://github.com/destiny-evidence/taxonomy-builder/issues/33) must add a mechanism to declare if a "published" version is a draft. Only non-draft versions should update the root project `index.json`.

### Size estimates

For a typical vocabulary with 100 concepts, ~1 broader and ~2 related refs per concept.

Per-concept breakdown (~400 bytes each):

| Field                  | Bytes |
| ---------------------- | ----- |
| UUID key               | ~38   |
| `pref_label`           | ~25   |
| `definition`           | ~90   |
| `scope_note`           | ~50   |
| `alt_labels` (1 label) | ~30   |
| `broader` (1 UUID)     | ~55   |
| `related` (2 UUIDs)    | ~95   |
| JSON punctuation       | ~20   |

Per-property breakdown (~120 bytes each):

| Field              | Bytes |
| ------------------ | ----- |
| UUID `id`          | ~38   |
| `identifier`       | ~20   |
| `label`            | ~20   |
| `description`      | ~50   |
| `domain_class_uri` | ~45   |
| `range_scheme_id`  | ~40   |
| `cardinality`      | ~15   |
| JSON punctuation   | ~15   |

File-level estimates:

|                                | Uncompressed | Gzipped  |
| ------------------------------ | ------------ | -------- |
| Vocabulary file (100 concepts) | ~40 KB       | ~8-10 KB |
| Ontology file (20 properties)  | ~4 KB        | ~1-2 KB  |
| Scheme index                   | <1 KB        | <1 KB    |
| Project index                  | <1 KB        | <1 KB    |

We can consider two versions of the vocabulary file if we need even lighter files, which might exclude things like related concepts and definitions.
