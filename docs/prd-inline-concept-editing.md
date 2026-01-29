# PRD: Inline Concept Editing

**Status:** Draft
**Created:** 2026-01-25
**Target Release:** TBD

## Problem Statement

Currently, editing a concept requires opening a modal dialog that:
- Covers the entire workspace, hiding the concept tree and broader context
- Breaks visual continuity between viewing and editing
- Feels heavyweight for quick edits (fixing typos, adjusting definitions)
- Requires multiple clicks and navigation steps (click concept → click edit → modal opens)

Users need to frequently reference the concept hierarchy while editing, but the modal workflow forces them to close the editor to see the tree, then reopen to continue editing.

## Goals

### Primary Goals
1. **Reduce cognitive load**: Keep the concept tree visible while editing
2. **Maintain context**: Keep spatial position and visual context during editing
3. **Simplify workflow**: Edit in the same visual space where concepts are consumed

### Non-Goals

1. Single-field inline editing with auto-save (future enhancement)
2. Batch editing multiple concepts simultaneously
3. Advanced relationship editing in tree view (broader/related management stays in detail panel)
4. Inline editing in tree nodes themselves (editing happens in detail panel)

## User Experience

### Current Flow
```
1. User selects concept in tree
2. ConceptDetail panel shows read-only view
3. User clicks "Edit" button
4. Modal opens with full form (covers everything)
5. User edits fields
6. User saves or cancels
7. Modal closes, back to read-only view
```

### Proposed Flow
```
1. User selects concept in tree
2. ConceptDetail panel shows read-only view
3. User clicks "Edit" button
4. Detail panel switches to edit mode (all fields become editable)
5. User edits fields directly in the detail panel
6. User clicks Save or Cancel
7. Detail panel returns to read-only view, tree remains visible throughout
```

### Key Improvement

The tree view stays visible during the entire editing process, eliminating the context-switching problem of the modal approach.

## Solution Design

### Approach: In-Panel Edit Mode

- Single "Edit" button toggles entire panel into edit mode
- All fields become editable simultaneously (like current modal, but in-panel)
- Save/Cancel buttons at bottom of panel
- **Pros**: Simple state management, familiar to current flow, tree stays visible
- **Cons**: Still edits all fields at once (but this is acceptable for initial version)

## Technical Architecture

### Component Changes

**ConceptDetail Component** (modify existing)

- Add edit mode state (`isEditing`)
- When in edit mode, render form controls (Input, Textarea) instead of static text
- Integrate form logic from existing ConceptForm:
  - Field state management
  - URI computation and preview
  - Validation
  - API integration for saving
- Add Save/Cancel action buttons
- Update props to include `onRefresh` callback (called after successful save)

**SchemeWorkspacePage** (modify existing)

- Remove modal-related state (`isFormOpen`, `editingConcept`)
- Remove modal-related handlers (`handleEdit`, `handleFormSuccess`, `handleFormClose`)
- Remove Modal component JSX for concept editing
- Pass `handleRefresh` to ConceptDetail component

**ConceptPane** (minor or no changes)

- Review to ensure adequate height for form controls
- May need scrolling adjustments

### State Management

**Local Component State** (in ConceptDetail)
```typescript
const [isEditing, setIsEditing] = useState(false);
const [prefLabel, setPrefLabel] = useState(concept.pref_label);
const [identifier, setIdentifier] = useState(concept.identifier ?? "");
const [definition, setDefinition] = useState(concept.definition ?? "");
const [scopeNote, setScopeNote] = useState(concept.scope_note ?? "");
const [altLabels, setAltLabels] = useState(concept.alt_labels);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

**Global State** (existing signals - no changes needed)
```typescript
selectedConcept.value  // Automatically updates when API returns new data
concepts.value         // Refreshes after successful save
```

### Existing Patterns to Leverage

1. **ConceptForm** - Reuse core logic:
   - Field validation
   - URI computation
   - Error handling patterns
   - API integration

2. **AltLabelsEditor** - Already inline-capable:
   - Reuse as-is in edit mode

3. **BroaderSelector/RelatedSelector** - Keep as-is:
   - Already inline within detail panel
   - No changes needed

4. **Input/Button Components** - Use existing:
   - Input component supports text and multiline
   - Button component for Save/Cancel

## Implementation Checklist

- [ ] Add edit mode state to ConceptDetail component
- [ ] Add form field state management (sync with concept prop)
- [ ] Implement save handler with API integration
- [ ] Implement cancel handler (resets fields)
- [ ] Update render logic to show form controls when editing
- [ ] Add Save/Cancel buttons
- [ ] Update component props (add `onRefresh`, remove `onEdit`)
- [ ] Remove modal state and handlers from SchemeWorkspacePage
- [ ] Remove Modal component JSX for concept editing
- [ ] Add CSS styles for edit mode layout
- [ ] Test edge cases (concept switching, validation errors, loading states)

## Edge Cases & Considerations

### Concept Changes While Editing

**Problem**: User starts editing concept A, then selects concept B in tree

**Solution**:

- useEffect with `concept.id` dependency exits edit mode and resets form
- Unsaved changes are lost (acceptable for MVP - can add warning in future)

### Validation Errors
**Problem**: User enters invalid data (e.g., duplicate identifier)

**Solution**:
- Display error message at top of form
- Keep form open with values intact
- User can retry or cancel

### Loading State
**Problem**: Save operation takes time

**Solution**:
- Disable Save button while loading
- Show "Saving..." text on button
- Loading state in parent prevents concept switching during save

### Long Text Fields
**Problem**: Definition/scope_note can be long, editing inline might feel cramped

**Solution**:
- Use textarea with reasonable default height
- Can be enhanced in future with expand/collapse or full-screen option

## Success Metrics

### Quantitative

- **Modal usage**: Concept edit modal usage drops to 0%
- **Error rate**: Failed saves remain same or decrease
- **No regressions**: Tree view, selection, and all other features continue working

### Qualitative
- User feedback: "I can see the tree while editing"
- User feedback: "Editing feels less disruptive"
- Developer feedback: "Code is maintainable and clean"

## Dependencies

### Technical Dependencies

- Existing API (`conceptsApi.update()`) - no changes needed
- Preact Signals for state management - already in place
- Component library (Input, Button, AltLabelsEditor) - already sufficient

### No New Dependencies

- No new npm packages needed
- No backend changes required
- No database migrations
- No new design patterns introduced

## Risks & Mitigations

**Low Risk Implementation**:
- Reusing existing ConceptForm logic (validation, URI computation, API calls)
- No API changes needed
- No changes to data model or backend
- Existing components handle all form needs

**Potential Issues**:

1. **Detail panel might feel cramped for long text**
   - Mitigation: Test early, adjust CSS or add expand option later

2. **Users might lose unsaved changes when switching concepts**
   - Mitigation: Acceptable for MVP, can add warning in future

3. **State management edge cases**
   - Mitigation: Loading state and disabled buttons prevent most issues

## Timeline

**Implementation**: 4-5 hours

- Component modifications: 2-3 hours
- Testing & edge cases: 1 hour
- Polish & bug fixes: 1 hour

**Testing**: Manual QA

- Basic edit flow (edit, save, cancel)
- Concept switching behavior
- Error handling
- Visual verification across screen sizes

## Future Enhancements

Once Phase 1 is proven successful, potential future improvements include:

- **Single-field inline editing**: Click-to-edit individual fields with auto-save
- **Unsaved changes warning**: Prompt before losing edits when switching concepts
- **Expand/collapse**: Full-screen editing option for long text fields
- **Keyboard shortcuts**: Enhanced navigation between fields
- **Optimistic updates**: Instant feedback before API confirmation

---

## Appendix: UI Mockups

### Current UI Flow
```
┌─────────────────────────────────────────┐
│ Tree View      │ Concept Detail         │
│                │                         │
│ > Project      │ Preferred Label: Foo   │
│   > Scheme     │ Definition: ...        │
│     • Concept1 │ [Edit] [Delete]        │
│     • Concept2 │                         │
│                │                         │
└─────────────────────────────────────────┘
                  ↓ Click Edit
┌──────────────────────────────────────────┐
│ ╔═══════════════════════════════════╗   │
│ ║       Edit Concept Modal          ║   │
│ ║                                   ║   │
│ ║  Preferred Label: [________]      ║   │
│ ║  Definition: [_____________]      ║   │
│ ║  Scope Note: [_____________]      ║   │
│ ║  ...                              ║   │
│ ║  [Cancel] [Save]                  ║   │
│ ╚═══════════════════════════════════╝   │
│  (Tree hidden behind modal)              │
└──────────────────────────────────────────┘
```

### Proposed UI Flow
```
┌─────────────────────────────────────────┐
│ Tree View      │ Concept Detail         │
│                │                         │
│ > Project      │ Preferred Label: Foo   │
│   > Scheme     │ Definition: ...        │
│     • Concept1 │ [Edit] [Delete]        │
│     • Concept2 │                         │
│                │                         │
└─────────────────────────────────────────┘
                  ↓ Click Edit
┌─────────────────────────────────────────┐
│ Tree View      │ Concept Detail         │
│                │ [Editing Mode]         │
│ > Project      │                         │
│   > Scheme     │ Preferred Label:       │
│     • Concept1 │ [Foo____________]       │
│     • Concept2 │                         │
│                │ Definition:             │
│ (Still visible)│ [Multi-line______]      │
│                │ [_________________]     │
│                │ Scope Note:             │
│                │ [Multi-line______]      │
│                │                         │
│                │ [Cancel] [Save Changes] │
└─────────────────────────────────────────┘
```

**Key Difference**: Tree remains visible throughout the entire editing process.
