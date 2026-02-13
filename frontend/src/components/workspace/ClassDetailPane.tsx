import { useState, useEffect, useRef } from "preact/hooks";
import { Button } from "../common/Button";
import { HistoryPanel } from "../history/HistoryPanel";
import { ontologyClasses } from "../../state/ontology";
import { properties, selectedPropertyId, creatingProperty } from "../../state/properties";
import { datatypeLabel } from "../../types/models";
import "./ClassDetailPane.css";

interface ClassDetailPaneProps {
  classUri: string;
  projectId: string;
  onPropertySelect: (propertyId: string) => void;
  onSchemeNavigate: (schemeId: string) => void;
}

export function ClassDetailPane({
  classUri,
  projectId,
  onPropertySelect,
  onSchemeNavigate,
}: ClassDetailPaneProps) {
  const [historyExpanded, setHistoryExpanded] = useState(false);
  const [sectionHeight, setSectionHeight] = useState(300);
  const isResizing = useRef(false);
  const startY = useRef(0);
  const startHeight = useRef(0);

  const ontologyClass = ontologyClasses.value.find((c) => c.uri === classUri);
  const classProperties = properties.value.filter((p) => p.domain_class === classUri);

  const classLabel = ontologyClass?.label ?? classUri;
  const classDescription = ontologyClass?.comment;

  function handleAddProperty() {
    creatingProperty.value = { projectId, domainClassUri: classUri };
    selectedPropertyId.value = null;
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
      const newHeight = Math.min(500, Math.max(100, startHeight.current + delta));
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

  return (
    <div class="class-detail-pane">
      <div class="class-detail-pane__header">
        <h2 class="class-detail-pane__title">{classLabel}</h2>
        {classDescription && (
          <p class="class-detail-pane__description">{classDescription}</p>
        )}
      </div>

      <div class="class-detail-pane__content">
        <div class="class-detail-pane__section">
          <div class="class-detail-pane__section-header">
            <h3 class="class-detail-pane__section-title">Properties</h3>
            <Button variant="ghost" size="sm" onClick={handleAddProperty}>
              + Add Property
            </Button>
          </div>

          {classProperties.length === 0 ? (
            <div class="class-detail-pane__empty">
              No properties defined for this class
            </div>
          ) : (
            <ul class="class-detail-pane__property-list">
              {classProperties.map((prop) => (
                <li
                  key={prop.id}
                  class={`class-detail-pane__property ${
                    selectedPropertyId.value === prop.id
                      ? "class-detail-pane__property--selected"
                      : ""
                  }`}
                >
                  <button
                    class="class-detail-pane__property-name"
                    onClick={() => onPropertySelect(prop.id)}
                  >
                    {prop.label}
                    {prop.required && (
                      <span class="class-detail-pane__required">*</span>
                    )}
                  </button>
                  <span class="class-detail-pane__property-range">
                    {prop.range_scheme ? (
                      <button
                        class="class-detail-pane__scheme-link"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSchemeNavigate(prop.range_scheme_id!);
                        }}
                      >
                        {prop.range_scheme.title}
                      </button>
                    ) : (
                      <span class="class-detail-pane__datatype">
                        {prop.range_datatype ? datatypeLabel(prop.range_datatype) : null}
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div class="class-detail-pane__footer">
        <button
          class={`class-detail-pane__section-header ${historyExpanded ? "class-detail-pane__section-header--expanded" : ""}`}
          onClick={() => setHistoryExpanded((v) => !v)}
          aria-expanded={historyExpanded}
        >
          <span class="class-detail-pane__section-arrow">
            {historyExpanded ? "▾" : "▸"}
          </span>
          History
        </button>
        {historyExpanded && (
          <div class="class-detail-pane__section-content" style={{ height: sectionHeight }}>
            <div
              class="class-detail-pane__resize-handle"
              onMouseDown={handleResizeStart}
            />
            <div class="class-detail-pane__section-scroll">
              <HistoryPanel source={{ type: "project", id: projectId }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
