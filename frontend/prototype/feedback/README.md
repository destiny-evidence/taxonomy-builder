# Feedback UI Prototype

Standalone HTML prototype for the taxonomy reader feedback system. No build step, no server — open `index.html` directly in a browser.

**GitHub issues**: #39 (submission), #40 (display), #41 (management)

## How to run

```
open frontend/prototype/feedback/index.html
```

## Tech stack

- Single self-contained HTML file (~1800 lines)
- **Preact** + **htm** from CDN (ESM imports, tagged templates)
- Inline CSS using design tokens matching `frontend/src/styles/variables.css`
- All data hardcoded — no API calls

### htm quirk

htm tagged templates do **not** decode HTML entities (`&#9654;`, `&#x1F50D;`, etc.). Use actual Unicode characters instead (e.g. `▶`, `⌕`, `✕`).

## Three views (tab bar)

### 1. Browser (Reader view)

The default view. Side-by-side layout:

- **Left sidebar**: project name, version dropdown, search box, collapsible concept scheme trees, Data Model section (classes + properties)
- **Right panel**: entity detail + feedback section

Selecting any entity in the sidebar shows its detail on the right. Entity types:

| Entity | Detail shows |
|--------|-------------|
| Concept | pref_label, definition, scope_note, alt_labels, broader/narrower links, related links |
| Scheme | title, description, concept count, top concepts list |
| Class | label, description, scope_note, properties using this class as domain |
| Property | label, description, domain class, range (scheme or datatype), cardinality |

**Feedback section** (below entity detail):
- **Drop box model**: readers only see their own feedback, not other people's. This avoids moderation liability for user-generated content and reduces dynamic content fetching. Duplicate submissions are a useful signal.
- Count badge and filter tabs (All / Open / Resolved) reflect only your own items
- Each item: date, feedback type badge, status badge, content
- Manager responses shown inline below the original
- Submit form (visible when authenticated): feedback type selector + text area
- Delete button on own comments (red, only when authenticated)
- Unauthenticated: no feedback visible, just a "Log in to submit feedback" prompt

### 2. Manager (Feedback Manager)

Dashboard for vocabulary managers to triage feedback.

- **Summary bar**: total count, open count, breakdown by entity type
- **Filter bar**: keyword search, entity type, feedback type, status dropdowns
- **Feedback cards**: entity label + type badge, scheme context, excerpt, author, date, status. Click to expand full content + response form
- **Response actions**: reply text field, Respond / Resolve / Decline buttons
- **Version context**: shows which snapshot version feedback was filed against

### 3. About (Project Landing)

- Project name, description, namespace
- Published version info (version number, date, publisher)
- Schemes list with concept counts
- Classes and properties summary counts

## Mock data

### Projects

Two projects with multiple versions:

| Project | Versions | Description |
|---------|----------|-------------|
| Demo Taxonomy | v1.0 (flat), v2.0 (hierarchical) | Colors with Warm/Cool categories in v2 |
| Study Designs | v1.0 | Study design types + evidence strength |

Version dropdown in the sidebar switches between published snapshots of the same project. Header has a segmented button group to switch between projects.

### Feedback items (8 total)

| ID | Project | Entity | Type | Status | Author |
|----|---------|--------|------|--------|--------|
| fb-001 | Demo | Red (concept) | Unclear definition | open | Dr. Maria Chen |
| fb-002 | Demo | Red (concept) | Missing term/area | responded | James Park |
| fb-003 | Demo | Colors (scheme) | Missing term/area | resolved | Dr. Alex Rivera |
| fb-004 | Demo | Investigation (class) | Structural question | open | Prof. Sarah Okonkwo |
| fb-005 | Demo | Risk Color (property) | Incorrect modelling | declined | Dr. Maria Chen |
| fb-006 | Demo | Turquoise (concept) | Scope question | open | James Park |
| fb-007 | Study | RCT (concept) | Missing term/area | open | Dr. Alex Rivera |
| fb-008 | Study | Evidence Strength (scheme) | Scope question | responded | Prof. Sarah Okonkwo |

Mock current user: **Dr. Maria Chen** (can delete fb-001 and fb-005).

### Feedback types by entity category

- **Concepts / Schemes**: Unclear definition, Missing term/area, Scope question, Overlap/duplication, General comment
- **Classes / Properties**: Incorrect modelling, Missing relationship, Structural question, General comment

### Feedback states

`open` → `responded` (manager replied) → `resolved` or `declined`

## Responsive design

Single CSS breakpoint at **768px**.

### Desktop (>768px)
- Browser: sidebar + detail panel side by side
- Manager: full dashboard layout
- About: centered content

### Mobile (≤768px)
- Browser uses **drill-down stack**: navigation list is the landing; tap an entity to push a full-screen detail view with back button
- Manager: still usable but designed for desktop (lives in the builder app)
- Tab bar scrolls horizontally if needed

## Search

### Sidebar search (Browser view)
- Searches entity labels, alt_labels, and feedback content/responses
- Results grouped by type (Concepts, Schemes, Classes, Properties, Feedback)
- Matching text highlighted
- Click a result to navigate to that entity (or the entity a feedback item is about)

### Manager search
- Keyword input in the filter bar
- Filters feedback by content, entity label, author, and response content
- Combines with dropdown filters (entity type, feedback type, status)

## Interactive features

- **Auth toggle** (header): switches between authenticated and anonymous states. When authenticated, you see your own feedback, the submit form, and delete buttons. When anonymous, feedback section is hidden entirely.
- **Version dropdown** (sidebar): switches between published versions of the current project
- **Project switcher** (header): segmented buttons to switch between Demo Taxonomy and Study Designs
- **Collapsible sections**: concept scheme trees, Data Model section, individual feedback cards in manager
- **Submit feedback** (mock): form accepts input and shows an alert — doesn't persist
- **Delete feedback**: confirmation dialog, removes from view (local state only)
- **Feedback count badges**: green circles on entities in sidebar showing your own feedback count (hidden when unauthenticated)
- **Status badges**: color-coded (yellow=open, blue=responded, green=resolved, grey=declined)

## Key constants

```js
DEMO_PROJECT_ID = "01965a00-0000-7000-8000-000000000000"
STUDY_PROJECT_ID = "02abc100-0000-7000-8000-000000000000"
MOCK_CURRENT_USER = "Dr. Maria Chen"
```

## Source data

The Demo Taxonomy mock data is based on the published format examples at:
- `docs/published-format/example/01965a00-.../1.0/vocabulary.json` (v1.0)
- `docs/published-format/example/01965a00-.../2.0/vocabulary.json` (v2.0)

The Study Designs project is entirely fabricated for the prototype.
