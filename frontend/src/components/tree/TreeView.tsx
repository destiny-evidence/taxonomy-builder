import { useState } from "preact/hooks";
import { useDroppable } from "@dnd-kit/core";
import {
  renderTree,
  treeLoading,
  expandedPaths,
  selectedConceptId,
  isDragging,
  buildRenderTree,
} from "../../state/concepts";
import { TreeNode } from "./TreeNode";
import { TreeDndProvider } from "./TreeDndProvider";
import type { TreeNode as TreeNodeType } from "../../types/models";
import "./TreeView.css";

interface TreeViewProps {
  schemeId: string;
  onRefresh?: () => void;
  onCreate?: () => void;
  onAddChild?: (parentId: string) => void;
  readOnly?: boolean;
  treeData?: TreeNodeType[];
}

export function TreeView({
  onRefresh,
  onCreate,
  onAddChild,
  readOnly = false,
  treeData,
}: TreeViewProps) {
  // Local expanded state for when treeData is provided externally
  const [localExpandedPaths, setLocalExpandedPaths] = useState<Set<string>>(new Set());

  // Use local state when treeData is provided, otherwise use global signal
  const useLocalState = treeData !== undefined;
  const currentExpandedPaths = useLocalState ? localExpandedPaths : expandedPaths.value;

  function handleToggle(path: string) {
    if (useLocalState) {
      setLocalExpandedPaths((prev) => {
        const newExpanded = new Set(prev);
        if (newExpanded.has(path)) {
          newExpanded.delete(path);
        } else {
          newExpanded.add(path);
        }
        return newExpanded;
      });
    } else {
      const newExpanded = new Set(expandedPaths.value);
      if (newExpanded.has(path)) {
        newExpanded.delete(path);
      } else {
        newExpanded.add(path);
      }
      expandedPaths.value = newExpanded;
    }
  }

  function handleSelect(conceptId: string) {
    if (!readOnly) {
      selectedConceptId.value = conceptId;
    }
  }

  // When treeData is provided, skip loading check
  if (!treeData && treeLoading.value) {
    return <div class="tree-view__loading">Loading tree...</div>;
  }

  // Use provided treeData or global signal
  const tree = treeData ? buildRenderTree(treeData) : renderTree.value;

  if (tree.length === 0) {
    return (
      <div class="tree-view__empty">
        <p>No concepts yet.{!readOnly && " Add your first concept to start building the taxonomy."}</p>
        {!readOnly && onCreate && (
          <button class="tree-view__add-button" onClick={onCreate}>
            + Add Concept
          </button>
        )}
      </div>
    );
  }

  const treeContent = (
    <div class="tree-view">
      {tree.map((node) => (
        <TreeNode
          key={node.path}
          node={node}
          expandedPaths={currentExpandedPaths}
          selectedId={readOnly ? null : selectedConceptId.value}
          onToggle={handleToggle}
          onSelect={handleSelect}
          onAddChild={readOnly ? undefined : onAddChild}
          readOnly={readOnly}
        />
      ))}

      {/* Root drop zone - visible when dragging (not in readOnly mode) */}
      {!readOnly && isDragging.value && <RootDropZone />}

      {!readOnly && onCreate && (
        <button class="tree-view__add-button" onClick={onCreate}>
          + Add Concept
        </button>
      )}
    </div>
  );

  // Always wrap with DndProvider (hooks require DndContext to function)
  // In readOnly mode, moves are effectively disabled via the readOnly prop on TreeNode
  return (
    <TreeDndProvider onMoveComplete={onRefresh ?? (() => {})}>
      {treeContent}
    </TreeDndProvider>
  );
}

function RootDropZone() {
  const { setNodeRef, isOver } = useDroppable({
    id: "root-drop-zone",
    data: { conceptId: "root", acceptsDrop: true },
  });

  return (
    <div
      ref={setNodeRef}
      class={`tree-view__root-drop ${isOver ? "tree-view__root-drop--over" : ""}`}
    >
      Drop here to make root concept
    </div>
  );
}
