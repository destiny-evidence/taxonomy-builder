import { Button } from "../common/Button";
import { searchQuery, hideNonMatches, expandMatchingPaths } from "../../state/search";
import { viewMode } from "../../state/graph";
import type { ViewMode } from "../../state/graph";
import "./TreeControls.css";

interface TreeControlsProps {
  onExpandAll: () => void;
  onCollapseAll: () => void;
}

export function TreeControls({ onExpandAll, onCollapseAll }: TreeControlsProps) {
  const query = searchQuery.value;
  const mode = viewMode.value;

  return (
    <div class="tree-controls">
      <div class="tree-controls__row">
        <div class="tree-controls__toggle">
          {(["tree", "graph"] as ViewMode[]).map((m) => (
            <button
              key={m}
              type="button"
              class={`tree-controls__toggle-btn${mode === m ? " tree-controls__toggle-btn--active" : ""}`}
              onClick={() => { viewMode.value = m; }}
            >
              {m === "tree" ? "Tree" : "Graph"}
            </button>
          ))}
        </div>
        <div class="tree-controls__search">
          <input
            type="text"
            class="tree-controls__search-input"
            placeholder="Search concepts..."
            value={query}
            onInput={(e) => {
              const newQuery = (e.target as HTMLInputElement).value;
              searchQuery.value = newQuery;
              expandMatchingPaths(newQuery);
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
      </div>
      {query && (
        <label class="tree-controls__hide-option">
          <input
            type="checkbox"
            checked={hideNonMatches.value}
            onChange={(e) => {
              hideNonMatches.value = (e.target as HTMLInputElement).checked;
            }}
          />
          Hide non-matches
        </label>
      )}
      {mode === "tree" && (
        <div class="tree-controls__buttons">
          <Button variant="ghost" size="sm" onClick={onExpandAll}>
            Expand All
          </Button>
          <Button variant="ghost" size="sm" onClick={onCollapseAll}>
            Collapse All
          </Button>
        </div>
      )}
    </div>
  );
}
