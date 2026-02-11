# Published Document Format

Static JSON format served to the taxonomy reader frontend, projected from `PublishedVersion.snapshot`. These are compressed to `.gz` at the blob level - this compression factor should be quite favourable as the majority of the data are `UUIDv7`s which have similar prefixes.

## Storage layout

```none
/{project-id}/
  index.json            # project metadata + version list
  {version-label}/      # e.g. "1.0/", "2.0-beta/"
    index.json          # vocabulary list for this version
    {scheme-id}.json    # concept data
  latest/               # copy of most recent non-draft version
    index.json          # UI default entrypoint
    {scheme-id}.json    # most recent concept data
```

The project index is regenerated whenever any vocabulary publishes a new version. Version directories and their contents are immutable once published. `latest/` is a copy of the most recent version's files, providing a direct and predictable interface for the UI to load by default.

## File types

Three file types, each with a JSON Schema definition:

### Project index (`project-index.schema.json`)

Served at `/{project-id}/index.json`. Contains current project metadata and a list of available versions with timestamps. Generally is not downloaded by the UI unless it needs to access a specific version, in which case it will use this to understand what is available.

### Version index (`version-index.schema.json`)

Served at `/{project-id}/{version-label}/index.json`. Lists the vocabularies included in this version with term counts and file references. `/{project-id}/latest/index.json` is the UI entrypoint.

### Vocabulary file (`vocabulary.schema.json`)

Served at `/{project-id}/{version-label}/{scheme-id}.json`. Contains scheme metadata and all concepts as a flat map keyed by UUID. Each concept carries `pref_label`, `definition`, `scope_note`, `alt_labels` (for search), `broader` (parent IDs), and `related` (related concept IDs). A `top_concepts` array lists root entry points for tree rendering.

This is normalized, meaning each concept's information is only represented once, but does require the client to build the tree in `O(n)` time.

## Considerations

### Future implications

Issue [#33](https://github.com/destiny-evidence/taxonomy-builder/issues/33) must add a mechanism to declare if a "published" version is a draft. Only if draft is False should `latest/` (unless there are no versions with `draft=False`).

### Size estimates

For a vocabulary with 1000 concepts, ~1 broader and ~2 related refs per concept.

Per-concept breakdown (~400 bytes each):

| Field | Bytes |
|---|---|
| UUID key | ~38 |
| `pref_label` | ~25 |
| `definition` | ~90 |
| `scope_note` | ~50 |
| `alt_labels` (1 label) | ~30 |
| `broader` (1 UUID) | ~55 |
| `related` (2 UUIDs) | ~95 |
| JSON punctuation | ~20 |

File-level estimates:

| | Uncompressed | Gzipped |
|---|---|---|
| Vocabulary file (1000 concepts) | ~400 KB | ~80-100 KB |
| Version index | <1 KB | <1 KB |
| Project index | <1 KB | <1 KB |
