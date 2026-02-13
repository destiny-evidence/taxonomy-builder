import { useDraggable, useDroppable } from "@dnd-kit/core";
import type { RenderNode } from "../../types/models";
import {
  isDragging,
  draggedConceptId,
  isValidDropTarget,
  getParentIdFromPath,
} from "../../state/concepts";
import { searchQuery } from "../../state/search";
import "./TreeNode.css";

interface TreeNodeProps {
  node: RenderNode;
  expandedPaths: Set<string>;
  selectedId: string | null;
  onToggle: (path: string) => void;
  onSelect: (conceptId: string) => void;
  onAddChild?: (parentId: string) => void;
  readOnly?: boolean;
}

export function TreeNode({
  node,
  expandedPaths,
  selectedId,
  onToggle,
  onSelect,
  onAddChild,
  readOnly = false,
}: TreeNodeProps) {
  const hasChildren = node.children.length > 0;
  const isExpanded = expandedPaths.has(node.path);
  const isSelected = selectedId === node.id;
  const currentParentId = getParentIdFromPath(node.path);

  // Draggable setup (disabled in readOnly mode)
  const {
    attributes,
    listeners,
    setNodeRef: setDragRef,
    isDragging: isThisDragging,
  } = useDraggable({
    id: `drag-${node.path}`,
    data: {
      conceptId: node.id,
      currentParentId,
      path: node.path,
    },
    disabled: readOnly,
  });

  // Droppable setup (disabled in readOnly mode)
  const draggedId = draggedConceptId.value;
  const canAcceptDrop = !readOnly && draggedId
    ? isValidDropTarget(node.id, draggedId, currentParentId)
    : false;

  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: `drop-${node.path}`,
    data: {
      conceptId: node.id,
      acceptsDrop: canAcceptDrop,
    },
    disabled: readOnly || !isDragging.value || !canAcceptDrop,
  });

  // Combine refs
  const setRefs = (el: HTMLElement | null) => {
    setDragRef(el);
    setDropRef(el);
  };

  // Search styling
  const isSearchActive = searchQuery.value.length > 0;
  const isMatch = node.matchStatus === "match";
  const isDimmed = isSearchActive && node.matchStatus === "none";

  const rowClasses = [
    "tree-node__row",
    isSelected && "tree-node__row--selected",
    isThisDragging && "tree-node__row--dragging",
    isDragging.value && !canAcceptDrop && draggedId !== node.id && "tree-node__row--invalid-drop",
    isOver && canAcceptDrop && "tree-node__row--drop-target",
    isMatch && "tree-node__row--match",
    isDimmed && "tree-node__row--dimmed",
  ]
    .filter(Boolean)
    .join(" ");

  // Cast attributes to avoid React/Preact type conflicts
  const dndAttributes = attributes as unknown as Record<string, unknown>;

  return (
    <div class="tree-node">
      <div
        ref={setRefs}
        class={rowClasses}
        style={{ paddingLeft: `${node.depth * 20 + 8}px` }}
        {...dndAttributes}
      >
        {!readOnly && (
          <span class="tree-node__drag-handle" title="Drag to move" {...listeners}>
            ⋮⋮
          </span>
        )}

        {hasChildren ? (
          <button
            class="tree-node__toggle"
            onClick={(e) => {
              e.stopPropagation();
              onToggle(node.path);
            }}
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? "▾" : "▸"}
          </button>
        ) : (
          <span class="tree-node__spacer" />
        )}

        <button
          class="tree-node__label"
          onClick={() => onSelect(node.id)}
          title={node.definition || undefined}
        >
          <span class="tree-node__text">{node.pref_label}</span>
          {node.hasMultipleParents && (
            <span
              class="tree-node__multi-parent"
              title={`Also under: ${node.otherParentLabels.join(", ")}`}
            >
              ⑂
            </span>
          )}
        </button>

        {!readOnly && onAddChild && (
          <button
            class="tree-node__add-child"
            onClick={(e) => {
              e.stopPropagation();
              onAddChild(node.id);
            }}
            aria-label="Add child"
            title="Add child concept"
          >
            +
          </button>
        )}
      </div>

      {hasChildren && isExpanded && (
        <div class="tree-node__children">
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              expandedPaths={expandedPaths}
              selectedId={selectedId}
              onToggle={onToggle}
              onSelect={onSelect}
              onAddChild={onAddChild}
              readOnly={readOnly}
            />
          ))}
        </div>
      )}
    </div>
  );
}
