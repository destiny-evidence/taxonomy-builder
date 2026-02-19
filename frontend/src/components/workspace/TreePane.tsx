import { useState } from "preact/hooks";
import { TreeView } from "../tree/TreeView";
import { TreeControls } from "../tree/TreeControls";
import { HistoryPanel } from "../history/HistoryPanel";
import { SchemeDetail } from "../schemes/SchemeDetail";
import { Button } from "../common/Button";
import { useResizeHandle } from "../../hooks/useResizeHandle";
import { currentScheme } from "../../state/schemes";
import { treeLoading } from "../../state/concepts";
import { historyVersion } from "../../state/history";
import "./TreePane.css";

type ExpandedSection = "history" | "schemeDetails" | null;

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
  const { height: sectionHeight, onResizeStart } = useResizeHandle();

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
        <div class="tree-pane__scheme-info">
          <h2 class="tree-pane__title">
            {scheme.title}
          </h2>
          {scheme.description && expandedSection !== "schemeDetails" && (
            <p class="tree-pane__description">{scheme.description}</p>
          )}
        </div>
        <div class="tree-pane__actions">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => toggleSection("schemeDetails")}
          >
            {expandedSection === "schemeDetails" ? "Hide Details" : "Show Details"}
          </Button>
          {onExport && (
            <Button variant="secondary" size="sm" onClick={onExport}>
              Export
            </Button>
          )}
        </div>
      </div>

      {expandedSection === "schemeDetails" && (
        <div class="tree-pane__scheme-detail">
          <SchemeDetail scheme={scheme} onRefresh={onRefresh} />
        </div>
      )}

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
            <div class="tree-pane__section-content" style={{ height: sectionHeight }}>
              <div
                class="tree-pane__resize-handle"
                onMouseDown={onResizeStart}
              />
              <div class="tree-pane__section-scroll">
                <HistoryPanel source={{ type: "scheme", id: schemeId }} refreshKey={historyVersion.value} />
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
