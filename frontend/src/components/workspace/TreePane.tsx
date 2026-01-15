import { TreeView } from "../tree/TreeView";
import { TreeControls } from "../tree/TreeControls";
import { Button } from "../common/Button";
import { currentScheme } from "../../state/schemes";
import { treeLoading } from "../../state/concepts";
import "./TreePane.css";

interface TreePaneProps {
  schemeId: string;
  onExpandAll: () => void;
  onCollapseAll: () => void;
  onRefresh: () => Promise<void>;
  onCreate?: () => void;
  onExport?: () => void;
}

export function TreePane({
  schemeId,
  onExpandAll,
  onCollapseAll,
  onRefresh,
  onCreate,
  onExport,
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
        <div class="tree-pane__header-main">
          <h2 class="tree-pane__title">{scheme.title}</h2>
          {scheme.description && (
            <p class="tree-pane__description">{scheme.description}</p>
          )}
        </div>
        <div class="tree-pane__actions">
          {onExport && (
            <Button variant="secondary" onClick={onExport}>
              Export
            </Button>
          )}
          {onCreate && <Button onClick={onCreate}>Add Concept</Button>}
        </div>
      </div>

      <TreeControls onExpandAll={onExpandAll} onCollapseAll={onCollapseAll} />

      <div class="tree-pane__content">
        <TreeView schemeId={schemeId} onRefresh={onRefresh} />
      </div>
    </div>
  );
}
