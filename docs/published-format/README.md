# Published Document Format

Static JSON format served to the taxonomy reader frontend. Separate from
the internal `PublishedVersion.snapshot` stored in the database — that
remains the archival source of truth, and this reader format is derived
from it at publish time.

## Storage layout

```
/{project-id}/
  index.json                          # project metadata + version list
  latest/                             # copy of most recent version
    index.json
    {scheme-id}.json
  {version-label}/                    # e.g. "1.0/", "2.0-beta/"
    index.json                        # vocabulary list for this version
    {scheme-id}.json                  # concept data
```

The project index is regenerated whenever any vocabulary publishes a new
version. Version directories and their contents are immutable once
published. `latest/` is a copy of the most recent version's files (not a
symlink/alias, since blob storage providers vary in alias support).

## File types

Three file types, each with a JSON Schema definition:

### Project index (`project-index.schema.json`)

Served at `/{project-id}/index.json`. Contains current project metadata
and a list of available versions with timestamps. This is the reader's
entry point.

### Version index (`version-index.schema.json`)

Served at `/{project-id}/{version-label}/index.json`. Lists the
vocabularies included in this version with term counts and file
references. Immutable once published. Handles schemes being
added/removed/renamed between versions.

### Vocabulary file (`vocabulary.schema.json`)

Served at `/{project-id}/{version-label}/{scheme-id}.json`. Contains
scheme metadata and all concepts as a flat map keyed by UUID. Each
concept carries `pref_label`, `definition`, `scope_note`, `alt_labels`,
`broader` (parent IDs), and `related` (related concept IDs). A
`root_concepts` array lists root entry points for tree rendering.

This requires the client to build the tree in `O(n)`.

## Why a flat map

Concepts are stored in a flat `{ [uuid]: concept }` map rather than a
nested tree structure. This avoids duplicating concepts that appear under
multiple parents (polyhierarchy), gives O(1) lookup by ID for detail
views and breadcrumbs, and lets the client build whatever view it
needs — tree browse, search results, or detail page — from the same data.

The client computes the tree by starting from `root_concepts` and walking
`broader` references. This is a single pass over the concept map and is
trivial for vocabularies in the low thousands.
