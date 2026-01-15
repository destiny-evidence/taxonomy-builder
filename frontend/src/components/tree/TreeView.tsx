import { useDroppable } from "@dnd-kit/core";
import {
  renderTree,
  treeLoading,
  expandedPaths,
  selectedConceptId,
  isDragging,
} from "../../state/concepts";
import { TreeNode } from "./TreeNode";
import { TreeDndProvider } from "./TreeDndProvider";
import "./TreeView.css";

interface TreeViewProps {
  schemeId: string;
  onRefresh: () => void;
  onCreate?: () => void;
}

export function TreeView({ onRefresh, onCreate }: TreeViewProps) {
  function handleToggle(path: string) {
    const newExpanded = new Set(expandedPaths.value);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    expandedPaths.value = newExpanded;
  }

  function handleSelect(conceptId: string) {
    selectedConceptId.value = conceptId;
  }

  if (treeLoading.value) {
    return <div class="tree-view__loading">Loading tree...</div>;
  }

  const tree = renderTree.value;

  if (tree.length === 0) {
    return (
      <div class="tree-view__empty">
        <p>No concepts yet. Add your first concept to start building the taxonomy.</p>
        {onCreate && (
          <button class="tree-view__add-button" onClick={onCreate}>
            + Add Concept
          </button>
        )}
      </div>
    );
  }

  return (
    <TreeDndProvider onMoveComplete={onRefresh}>
      <div class="tree-view">
        {tree.map((node) => (
          <TreeNode
            key={node.path}
            node={node}
            expandedPaths={expandedPaths.value}
            selectedId={selectedConceptId.value}
            onToggle={handleToggle}
            onSelect={handleSelect}
          />
        ))}

        {/* Root drop zone - visible when dragging */}
        {isDragging.value && <RootDropZone />}

        {onCreate && (
          <button class="tree-view__add-button" onClick={onCreate}>
            + Add Concept
          </button>
        )}
      </div>
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
