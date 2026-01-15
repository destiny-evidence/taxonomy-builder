# PRD: Three-Pane Layout

## Summary

Introduce a three-pane workspace layout for the scheme editing view that provides scheme navigation within a project and better use of horizontal space.

## Current State

- **ProjectsPage** (`/`): Project cards
- **ProjectDetailPage** (`/projects/:id`): Scheme cards for selected project
- **SchemeDetailPage** (`/schemes/:id`): Two-pane layout (tree + sidebar with tabs)

**Pain points:**

- Schemes are isolated - switching requires navigating back to project page
- Tree pane has excess horizontal space on wide screens
- Navigation requires multiple page transitions

## Target State

A three-pane workspace at `/projects/:project_id/schemes/:scheme_id`:

```text
+------------------+------------------------+---------------------+
|                  |                        |                     |
|  SCHEMES         |  TREE                  |  CONCEPT            |
|  [Project ▼]     |                        |                     |
|                  |  [Scheme Header]       |  Details tab        |
|  - Scheme A      |  - Add Concept         |  shows selected     |
|  - Scheme B *    |  - Export              |  concept info       |
|  - Scheme C      |  - History / Versions  |                     |
|                  |                        |                     |
|  + New Scheme    |  [TreeView]            |                     |
|                  |  + Concept 1           |                     |
|                  |    - Concept 1.1 *     |                     |
|                  |  + Concept 2           |                     |
|                  |                        |                     |
+------------------+------------------------+---------------------+
     ~280px              flex-grow                 ~380px
```

## Key Changes

### 1. Three-Pane Layout

| Pane   | Content                                   | Width     |
| ------ | ----------------------------------------- | --------- |
| Left   | Project dropdown + scrollable scheme list | ~280px    |
| Middle | Scheme header + TreeView                  | flex-grow |
| Right  | Concept details (current sidebar content) | ~380px    |

### 2. Scheme Navigation in Left Pane

- Header shows current project name with dropdown to switch projects
- Body shows list of schemes in the selected project
- Clicking a scheme navigates to it
- "New Scheme" button at bottom

### 3. History/Versions Relocated

Move from right pane tabs to scheme header area:

- Access via buttons/dropdown in scheme header
- Keeps the right pane focused on concept details
- Clarifies that History/Versions are scheme-level concerns

### 4. URL Structure

- `/projects/:project_id/schemes/:scheme_id` - workspace view
- `/projects/:project_id` - project detail (current behavior, or redirect to first scheme)
- `/` - project list (unchanged)

## Out of Scope

- Inline concept editing (separate PRD)
- Responsive/mobile behavior (future consideration)
- Pane resizing

## Verification

1. Open a scheme - see three panes with schemes list on left
2. Click a different scheme in left pane - tree updates
3. Use project dropdown - schemes list updates for new project
4. Access History/Versions from scheme header
5. Deep link to `/projects/X/schemes/Y` loads correct state
