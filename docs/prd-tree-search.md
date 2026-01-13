# PRD: Tree Search

## Overview

Add search functionality to the tree browser, allowing users to quickly find concepts by searching across labels. Matching concepts are highlighted and non-matching concepts can be greyed out or hidden.

## Problem

As taxonomies grow, users struggle to locate specific concepts in the tree. Scrolling and manually expanding branches is time-consuming, especially for large or deep hierarchies.

Users need to quickly find concepts by name, including alternative labels (synonyms, abbreviations). Without search, productivity suffers and users may create duplicate concepts because they can't find existing ones.

## Requirements

### MVP (Phase 1)

1. **Search input** - Text field in the tree panel to enter search queries
2. **Search scope** - Match against `pref_label` and `alt_labels`
3. **Case-insensitive matching** - "dog" matches "Dogs", "DOG", etc.
4. **Auto-expand ancestors** - When a concept matches, expand all ancestor nodes to reveal it
5. **Highlight matches** - Visually distinguish matching concepts
6. **Hide non-matches option** - Checkbox to hide non-matching concepts (default: off)
   - **Default (unchecked)**: Non-matching concepts are greyed out but visible (preserves context)
   - **Checked**: Non-matching concepts are hidden (focused view)
7. **Clear search** - Button/action to clear search and show full tree
8. **Preserve expansion** - After clearing search, keep nodes expanded (don't restore previous state)

### Phase 2 (Future)

1. **Extended search fields** - Search across `definition` and `scope_note`
2. **Search operators** - Exact match with quotes, field-specific search (e.g., `alt:synonym`)
3. **Match highlighting** - Highlight the matching substring within labels
4. **Search history** - Recent searches dropdown
5. **Keyboard navigation** - Arrow keys to jump between matches

## Constraints

- **Client-side filtering** - Filter the already-loaded tree data in the browser. No backend changes required for MVP.
- **Performance** - Should remain responsive for taxonomies up to ~10,000 concepts
- **Accessibility** - Search input should be keyboard-accessible with appropriate ARIA attributes

## UI Design

### Search Controls

```text
┌─────────────────────────────────────────┐
│ [🔍 Search concepts...        ] [Clear] │
│ [ ] Hide non-matches                    │
├─────────────────────────────────────────┤
│ [Expand All] [Collapse All]             │
├─────────────────────────────────────────┤
│ ▾ Animals                               │
│   ▾ Mammals                             │
│     ▸ Cats                              │
│     ▸ Dogs  ← highlighted match         │
│   ▸ Birds (greyed out)                  │
│ ▸ Plants (greyed out)                   │
└─────────────────────────────────────────┘
```

### Visual States

| State                | Visual Treatment                                    |
| -------------------- | --------------------------------------------------- |
| Match                | Background highlight (e.g., light yellow)           |
| Non-match (grey out) | Reduced opacity (e.g., 40%), greyed text            |
| Non-match (hide)     | Hidden from view                                    |
| Ancestor of match    | Normal appearance (not highlighted, not greyed)     |

## Out of Scope

- Server-side search API (may be needed later for very large taxonomies)
- Full-text search indexing
- Fuzzy/typo-tolerant matching
- Search within concept URIs or identifiers
- Regex search

## Success Criteria

1. User can type in search box and see matching concepts highlighted within 100ms
2. Ancestors of matching concepts are automatically expanded
3. User can toggle "hide non-matches" checkbox to switch between grey-out and hide modes
4. Clearing search leaves tree in current expanded state
5. Search matches against both pref_label and alt_labels
6. Empty search shows full tree with no filtering
7. Works smoothly with taxonomies of 1,000+ concepts
