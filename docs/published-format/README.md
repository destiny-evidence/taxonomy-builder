# Published Document Format

Static JSON format served to the taxonomy reader frontend, projected from `PublishedVersion.snapshot`. These are compressed to `.gz` at the blob level - this compression factor should be quite favourable as the majority of the data are `UUIDv7`s which have similar prefixes.

## Storage layout

Each scheme is versioned independently.

```none
/{project-id}/
  index.json                  # project metadata + list of schemes
  {scheme-id}/
    index.json                # scheme metadata + version list
    {version-label}.json      # concept data for a specific version
```

The project index is regenerated whenever any scheme publishes a new version. Version files are immutable once published. The project index carries `latest_version` per scheme, so the reader constructs the path to the latest vocabulary file directly as `{scheme-id}/{latest_version}.json`.

### Reader flow

1. Fetch `/{project-id}/index.json` — render scheme list
2. User picks a scheme — fetch `/{project-id}/{scheme-id}/{latest_version}.json` — render concepts
3. (Optional) User wants a different version — fetch `/{project-id}/{scheme-id}/index.json` — show version picker — fetch `/{project-id}/{scheme-id}/{version-label}.json`

## File types

Three file types, each with a JSON Schema definition:

### Project index (`project-index.schema.json`)

Served at `/{project-id}/index.json`. Contains current project metadata and a list of published schemes with their latest version label and term count. This is the reader's entry point.

### Scheme index (`scheme-index.schema.json`)

Served at `/{project-id}/{scheme-id}/index.json`. Lists available versions of a scheme with release notes. Only loaded on demand when the reader needs to switch versions.

### Vocabulary file (`vocabulary.schema.json`)

Served at `/{project-id}/{scheme-id}/{version-label}.json`. Contains scheme metadata and all concepts as a flat map keyed by UUID. Each concept carries `pref_label`, `definition`, `scope_note`, `alt_labels` (for search), `broader` (parent IDs), and `related` (related concept IDs). A `top_concepts` array lists root entry points for tree rendering.

This is normalized, meaning each concept's information is only represented once, but does require the client to build the tree in `O(n)` time.

## Considerations

### Future implications

Issue [#33](https://github.com/destiny-evidence/taxonomy-builder/issues/33) must add a mechanism to declare if a "published" version is a draft. Only non-draft versions should be reflected in the project index's `latest_version` field.

### Size estimates

For a large vocabulary with 1000 concepts, ~1 broader and ~2 related refs per concept.

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

File-level estimates:

|                                 | Uncompressed | Gzipped    |
| ------------------------------- | ------------ | ---------- |
| Vocabulary file (1000 concepts) | ~400 KB      | ~80-100 KB |
| Scheme index                    | <1 KB        | <1 KB      |
| Project index                   | <1 KB        | <1 KB      |
