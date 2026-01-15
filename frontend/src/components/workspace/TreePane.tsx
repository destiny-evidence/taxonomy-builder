import { useState } from "preact/hooks";
import { TreeView } from "../tree/TreeView";
import { TreeControls } from "../tree/TreeControls";
import { HistoryPanel } from "../history/HistoryPanel";
import { VersionsPanel } from "../versions/VersionsPanel";
import { Button } from "../common/Button";
import { currentScheme } from "../../state/schemes";
import { treeLoading } from "../../state/concepts";
import "./TreePane.css";

type ExpandedSection = "history" | "versions" | null;

interface TreePaneProps {
  schemeId: string;
  onExpandAll: () => void;
  onCollapseAll: () => void;
  onRefresh: () => Promise<void>;
  onCreate?: () => void;
  onAddChild?: (parentId: string) => void;
  onExport?: () => void;
}

export function TreePane({
  schemeId,
  onExpandAll,
  onCollapseAll,
  onRefresh,
  onCreate,
  onAddChild,
  onExport,
}: TreePaneProps) {
  const [expandedSection, setExpandedSection] = useState<ExpandedSection>(null);

  const scheme = currentScheme.value;
  const isLoading = treeLoading.value;

  function toggleSection(section: ExpandedSection) {
    setExpandedSection((current) => (current === section ? null : section));
  }

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
        </div>
      </div>

      <TreeControls onExpandAll={onExpandAll} onCollapseAll={onCollapseAll} />

      <div class="tree-pane__content">
        <TreeView
          schemeId={schemeId}
          onRefresh={onRefresh}
          onCreate={onCreate}
          onAddChild={onAddChild}
        />
      </div>

      <div class="tree-pane__footer">
        <div class="tree-pane__section">
          <button
            class={`tree-pane__section-header ${expandedSection === "history" ? "tree-pane__section-header--expanded" : ""}`}
            onClick={() => toggleSection("history")}
            aria-expanded={expandedSection === "history"}
          >
            <span class="tree-pane__section-arrow">
              {expandedSection === "history" ? "▾" : "▸"}
            </span>
            History
          </button>
          {expandedSection === "history" && (
            <div class="tree-pane__section-content">
              <HistoryPanel schemeId={schemeId} />
            </div>
          )}
        </div>

        <div class="tree-pane__section">
          <button
            class={`tree-pane__section-header ${expandedSection === "versions" ? "tree-pane__section-header--expanded" : ""}`}
            onClick={() => toggleSection("versions")}
            aria-expanded={expandedSection === "versions"}
          >
            <span class="tree-pane__section-arrow">
              {expandedSection === "versions" ? "▾" : "▸"}
            </span>
            Versions
          </button>
          {expandedSection === "versions" && (
            <div class="tree-pane__section-content">
              <VersionsPanel schemeId={schemeId} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
