import { Button } from "../common/Button";
import { searchQuery } from "../../state/search";
import "./TreeControls.css";

interface TreeControlsProps {
  onExpandAll: () => void;
  onCollapseAll: () => void;
}

export function TreeControls({ onExpandAll, onCollapseAll }: TreeControlsProps) {
  const query = searchQuery.value;

  return (
    <div class="tree-controls">
      <div class="tree-controls__search">
        <input
          type="text"
          class="tree-controls__search-input"
          placeholder="Search concepts..."
          value={query}
          onInput={(e) => {
            searchQuery.value = (e.target as HTMLInputElement).value;
          }}
        />
        {query && (
          <button
            type="button"
            class="tree-controls__clear-btn"
            aria-label="Clear search"
            onClick={() => {
              searchQuery.value = "";
            }}
          >
            ×
          </button>
        )}
      </div>
      <div class="tree-controls__buttons">
        <Button variant="ghost" size="sm" onClick={onExpandAll}>
          Expand All
        </Button>
        <Button variant="ghost" size="sm" onClick={onCollapseAll}>
          Collapse All
        </Button>
      </div>
    </div>
  );
}
