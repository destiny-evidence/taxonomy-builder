# PRD: Drag-and-Drop Reordering

## Overview

Enable users to reorganize the taxonomy hierarchy by dragging and dropping concepts in the tree view, providing an intuitive way to restructure broader/narrower relationships.

## Problem

Currently, changing a concept's position in the hierarchy requires:

1. Opening the concept
2. Removing existing broader relationships
3. Adding new broader relationships

This is cumbersome for reorganization tasks. Users expect to drag concepts to new positions, especially when restructuring taxonomies.

## Requirements

### Drag Operations

1. **Move concept to new parent:**
   - Drag concept onto another concept
   - Creates broader relationship with drop target
   - Removes broader relationship with previous parent (if single parent)

2. **Move concept to root:**
   - Drag concept to empty space or "root" drop zone
   - Removes all broader relationships
   - Concept becomes a top-level concept

### Visual Feedback

1. **Drag preview:** Ghost/outline of dragged concept
2. **Drop indicators:**
   - Highlight valid drop targets
   - Show insertion line for sibling reordering
3. **Invalid drop:** Visual indication when drop not allowed

### Constraints

1. **Cannot drop on self**
2. **Cannot drop on descendant** (would create cycle)
3. **Cannot drop on current parent** (no-op)

### Polyhierarchy Behavior

Since concepts can have multiple parents:

- **Default:** Move replaces the parent in current tree path
- **With modifier key (Alt/Option):** Add as additional parent (keep existing)

## Data Model Changes

## API Changes

### Move Concept

```
POST /api/concepts/{id}/move
{
  "new_parent_id": "uuid" | null,  // null = move to root
  "previous_parent_id": "uuid" | null,  // which parent to replace (for polyhierarchy)
}
```

**Response:**

```json
{
  "success": true,
  "concept": { /* updated concept */ }
}
```

## Technical Implementation

### Frontend

**Library options:**

- `@dnd-kit/core` - Modern, accessible, works with Preact
- Native HTML5 drag-and-drop - No dependencies, but less polished
- `preact-dnd` - Preact-specific wrapper

Recommend **@dnd-kit** for accessibility and flexibility.

**Tree node changes:**

```tsx
function TreeNode({ node, onMove }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: node.path,
    data: { conceptId: node.id, parentPath: getParentPath(node.path) }
  });

  const { setNodeRef: dropRef, isOver } = useDroppable({
    id: `drop-${node.path}`,
    data: { conceptId: node.id }
  });

  return (
    <div ref={setNodeRef} {...attributes} {...listeners}>
      <div ref={dropRef} class={isOver ? "drop-target" : ""}>
        {node.pref_label}
      </div>
      {/* children */}
    </div>
  );
}
```

**Cycle detection:**

```typescript
function isDescendant(draggedId: string, targetId: string, tree: TreeNode[]): boolean {
  // Walk tree to check if targetId is under draggedId
  function check(nodes: TreeNode[], underDragged: boolean): boolean {
    for (const node of nodes) {
      if (node.id === draggedId) {
        return check(node.children, true);
      }
      if (underDragged && node.id === targetId) {
        return true;
      }
      if (check(node.children, underDragged)) {
        return true;
      }
    }
    return false;
  }
  return check(tree, false);
}
```

### Backend

**Move service method:**

```python
async def move_concept(
    self,
    concept_id: UUID,
    new_parent_id: UUID | None,
    previous_parent_id: UUID | None,
    position: int,
) -> Concept:
    concept = await self.get(concept_id)

    # Validate: not moving to self
    if new_parent_id == concept_id:
        raise ValueError("Cannot move concept to itself")

    # Validate: not moving to descendant
    if new_parent_id and await self._is_descendant(concept_id, new_parent_id):
        raise ValueError("Cannot move concept to its own descendant")

    # Remove old parent relationship
    if previous_parent_id:
        await self._remove_broader(concept_id, previous_parent_id)

    # Add new parent relationship
    if new_parent_id:
        await self._add_broader(concept_id, new_parent_id, position)
    else:
        # Moving to root
        concept.root_sort_order = position

    return concept
```

## UI/UX Details

### Drag Handle

Option A: Entire row is draggable
Option B: Explicit drag handle icon (⋮⋮)

Recommend **Option B** for clarity and to avoid accidental drags.

### Drop Zones

```
[▸] Animals
    ┌─────────────────────┐  
    │ [⋮⋮] Mammals       │  ← Drop on (make child)
    └─────────────────────┘
```

### Modifier Key Behavior

| Action | Result |
|--------|--------|
| Drop on concept | Replace current parent with drop target |
| Alt + Drop on concept | Add drop target as additional parent |
| Drop on root zone | Remove from current parent, make root |

### Keyboard Support (Stretch)

- Arrow keys to select concept
- Ctrl+X to cut, Ctrl+V to paste as child
- Ctrl+Shift+V to paste as sibling

## Out of Scope

- Drag multiple concepts at once
- Drag between schemes
- Undo drag operation (use version history revert instead)
- Touch/mobile drag support (desktop first)
- Reordering

## Success Criteria

- Users can drag a concept to a new parent
- Users can drag a concept to root level
- Users can reorder siblings via drag
- Invalid drops (self, descendant) are prevented with visual feedback
- Tree updates immediately after drop
- Change is recorded in version history
