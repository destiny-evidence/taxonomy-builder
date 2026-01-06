import { renderTree, treeLoading, expandedPaths, selectedConceptId } from "../../state/concepts";
import { TreeNode } from "./TreeNode";
import "./TreeView.css";

interface TreeViewProps {
  schemeId: string;
}

export function TreeView(_props: TreeViewProps) {
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
      </div>
    );
  }

  return (
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
    </div>
  );
}
