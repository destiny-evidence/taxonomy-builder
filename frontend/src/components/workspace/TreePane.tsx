import { TreeView } from "../tree/TreeView";
import { TreeControls } from "../tree/TreeControls";
import { currentScheme } from "../../state/schemes";
import { treeLoading } from "../../state/concepts";
import "./TreePane.css";

interface TreePaneProps {
  schemeId: string;
  onExpandAll: () => void;
  onCollapseAll: () => void;
  onRefresh: () => Promise<void>;
}

export function TreePane({
  schemeId,
  onExpandAll,
  onCollapseAll,
  onRefresh,
}: TreePaneProps) {
  const scheme = currentScheme.value;
  const isLoading = treeLoading.value;

  if (!scheme || isLoading) {
    return (
      <div class="tree-pane">
        <div class="tree-pane__loading">Loading...</div>
      </div>
    );
  }

  return (
    <div class="tree-pane">
      <div class="tree-pane__header">
        <h2 class="tree-pane__title">{scheme.title}</h2>
      </div>

      <TreeControls onExpandAll={onExpandAll} onCollapseAll={onCollapseAll} />

      <div class="tree-pane__content">
        <TreeView schemeId={schemeId} onRefresh={onRefresh} />
      </div>
    </div>
  );
}
