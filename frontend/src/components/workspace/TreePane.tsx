import { useState, useEffect, useRef } from "preact/hooks";
import { TreeView } from "../tree/TreeView";
import { TreeControls } from "../tree/TreeControls";
import { HistoryPanel } from "../history/HistoryPanel";
import { VersionsPanel } from "../versions/VersionsPanel";
import { SchemeDetail } from "../schemes/SchemeDetail";
import { Button } from "../common/Button";
import { currentScheme } from "../../state/schemes";
import { treeLoading } from "../../state/concepts";
import "./TreePane.css";

type ExpandedSection = "history" | "versions" | "schemeDetails" | null;

const MIN_SECTION_HEIGHT = 100;
const MAX_SECTION_HEIGHT = 500;
const DEFAULT_SECTION_HEIGHT = 300;

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
  const [sectionHeight, setSectionHeight] = useState(DEFAULT_SECTION_HEIGHT);
  const isResizing = useRef(false);
  const startY = useRef(0);
  const startHeight = useRef(0);

  const scheme = currentScheme.value;
  const isLoading = treeLoading.value;

  function toggleSection(section: ExpandedSection) {
    setExpandedSection((current) => (current === section ? null : section));
  }

  function handleResizeStart(e: MouseEvent) {
    e.preventDefault();
    isResizing.current = true;
    startY.current = e.clientY;
    startHeight.current = sectionHeight;
    document.body.style.userSelect = "none";
  }

  useEffect(() => {
    function handleMouseMove(e: MouseEvent) {
      if (!isResizing.current) return;
      const delta = startY.current - e.clientY;
      const newHeight = Math.min(
        MAX_SECTION_HEIGHT,
        Math.max(MIN_SECTION_HEIGHT, startHeight.current + delta)
      );
      setSectionHeight(newHeight);
    }

    function handleMouseUp() {
      if (isResizing.current) {
        isResizing.current = false;
        document.body.style.userSelect = "";
      }
    }

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

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
            {scheme.version && (
              <span class="tree-pane__version">{scheme.version}</span>
            )}
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
                onMouseDown={handleResizeStart}
              />
              <div class="tree-pane__section-scroll">
                <HistoryPanel schemeId={schemeId} />
              </div>
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
            <div class="tree-pane__section-content" style={{ height: sectionHeight }}>
              <div
                class="tree-pane__resize-handle"
                onMouseDown={handleResizeStart}
              />
              <div class="tree-pane__section-scroll">
                <VersionsPanel schemeId={schemeId} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
