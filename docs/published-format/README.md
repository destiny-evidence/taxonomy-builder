# Published Document Format

Static JSON format served to the taxonomy reader frontend. Separate from
the internal `PublishedVersion.snapshot` stored in the database — that
remains the archival source of truth, and this reader format is derived
from it at publish time.

## Structure

Two file types, chunked at vocabulary level:

**Index file** (`index.schema.json`) — one per project. Contains project
metadata and a list of published vocabularies with term counts and file
references. This is the reader's entry point.

**Vocabulary file** (`vocabulary.schema.json`) — one per concept scheme.
Contains scheme metadata and all concepts as a flat map keyed by UUID.
Each concept carries `pref_label`, `definition`, `scope_note`,
`alt_labels`, `broader` (parent IDs), and `related` (related concept IDs).
A `top_concepts` array lists root entry points for tree rendering.

## Why a flat map

Concepts are stored in a flat `{ [uuid]: concept }` map rather than a
nested tree structure. This avoids duplicating concepts that appear under
multiple parents (polyhierarchy), gives O(1) lookup by ID for detail views
and breadcrumbs, and lets the client build whatever view it needs — tree
browse, search results, or detail page — from the same data.

The client computes the tree by starting from `top_concepts` and walking
`broader` references. This is a single pass over the concept map and is
trivial for vocabularies in the low thousands.

## Upgrade path to a tree skeleton

If client-side tree building becomes a performance concern at larger
vocabulary sizes, the format can be extended with a lightweight `tree`
field — a nested structure carrying only IDs and ordering:

```json
{
  "tree": [
    { "id": "uuid-1", "children": [
      { "id": "uuid-2", "children": [] }
    ]}
  ]
}
```

This is additive and backwards-compatible. The concept map stays as-is
(it's still needed for detail views and search), and `top_concepts`
becomes redundant since the tree roots serve the same purpose. The client
renders by walking the tree skeleton and looking up concept data from the
map.
