import { Button } from "../common/Button";
import "./TreeControls.css";

interface TreeControlsProps {
  onExpandAll: () => void;
  onCollapseAll: () => void;
}

export function TreeControls({ onExpandAll, onCollapseAll }: TreeControlsProps) {
  return (
    <div class="tree-controls">
      <Button variant="ghost" size="sm" onClick={onExpandAll}>
        Expand All
      </Button>
      <Button variant="ghost" size="sm" onClick={onCollapseAll}>
        Collapse All
      </Button>
    </div>
  );
}
