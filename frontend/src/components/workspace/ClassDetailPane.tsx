import { Fragment } from "preact";
import { useState } from "preact/hooks";
import { Button } from "../common/Button";
import { ClassDetail } from "../classes/ClassDetail";
import { HistoryPanel } from "../history/HistoryPanel";
import { useResizeHandle } from "../../hooks/useResizeHandle";
import { ontologyClasses, selectedClassUri } from "../../state/classes";
import { properties, selectedPropertyId, creatingProperty } from "../../state/properties";
import { extractLocalName } from "../../utils/strings";
import { historyVersion } from "../../state/history";
import { datatypeLabel } from "../../types/models";
import "./ClassDetailPane.css";

interface ClassDetailPaneProps {
  classUri: string;
  projectId: string;
  onPropertySelect: (propertyId: string) => void;
  onSchemeNavigate: (schemeId: string) => void;
  onRefresh: () => void;
  onClassDeleted: () => void;
}

export function ClassDetailPane({
  classUri,
  projectId,
  onPropertySelect,
  onSchemeNavigate,
  onRefresh,
  onClassDeleted,
}: ClassDetailPaneProps) {
  const [historyExpanded, setHistoryExpanded] = useState(false);
  const { height: sectionHeight, onResizeStart } = useResizeHandle();

  const ontologyClass = ontologyClasses.value.find((c) => c.uri === classUri);
  const classProperties = properties.value.filter((p) => p.domain_class_uris.includes(classUri));
  const rangeProperties = properties.value.filter(
    (p) => p.range_class === classUri && !p.domain_class_uris.includes(classUri),
  );

  function handleAddProperty() {
    creatingProperty.value = { projectId, domainClassUri: classUri };
    selectedPropertyId.value = null;
  }

  return (
    <div class="class-detail-pane">
      <div class="class-detail-pane__header">
        {ontologyClass ? (
          <ClassDetail
            key={ontologyClass.id}
            ontologyClass={ontologyClass}
            onRefresh={onRefresh}
            onDeleted={onClassDeleted}
          />
        ) : (
          <h2 class="class-detail-pane__title">{classUri}</h2>
        )}
      </div>

      <div class="class-detail-pane__content">
        {ontologyClass && (ontologyClass.superclass_uris.length > 0 || ontologyClass.subclass_uris.length > 0) ? (
          <div class="class-detail-pane__section">
            <div class="class-detail-pane__section-header">
              <h3 class="class-detail-pane__section-title">Hierarchy</h3>
            </div>
            {ontologyClass.superclass_uris.length > 0 && (
              <div class="class-detail-pane__field">
                <span class="class-detail-pane__field-label">Superclass: </span>
                {ontologyClass.superclass_uris.map((uri, i) => {
                  const cls = ontologyClasses.value.find((c) => c.uri === uri);
                  return (
                    <Fragment key={uri}>
                      {i > 0 && ", "}
                      {cls ? (
                        <button
                          class="class-detail-pane__class-link"
                          onClick={(e) => {
                            e.stopPropagation();
                            selectedClassUri.value = uri;
                          }}
                        >
                          {cls.label}
                        </button>
                      ) : (
                        <span class="class-detail-pane__class-external">{extractLocalName(uri)}</span>
                      )}
                    </Fragment>
                  );
                })}
              </div>
            )}
            {ontologyClass.subclass_uris.length > 0 && (
              <div class="class-detail-pane__field">
                <span class="class-detail-pane__field-label">Subclasses: </span>
                {ontologyClass.subclass_uris.map((uri, i) => {
                  const cls = ontologyClasses.value.find((c) => c.uri === uri);
                  return (
                    <Fragment key={uri}>
                      {i > 0 && ", "}
                      {cls ? (
                        <button
                          class="class-detail-pane__class-link"
                          onClick={(e) => {
                            e.stopPropagation();
                            selectedClassUri.value = uri;
                          }}
                        >
                          {cls.label}
                        </button>
                      ) : (
                        <span class="class-detail-pane__class-external">{extractLocalName(uri)}</span>
                      )}
                    </Fragment>
                  );
                })}
              </div>
            )}
          </div>
        ) : null}

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
                    ) : prop.range_class ? (
                      <span class="class-detail-pane__datatype">
                        {ontologyClasses.value.find((c) => c.uri === prop.range_class)?.label ?? prop.range_class}
                      </span>
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

        {rangeProperties.length > 0 && (
          <div class="class-detail-pane__section">
            <div class="class-detail-pane__section-header">
              <h3 class="class-detail-pane__section-title">Referenced by</h3>
            </div>
            <ul class="class-detail-pane__property-list">
              {rangeProperties.map((prop) => (
                <li key={prop.id} class="class-detail-pane__property">
                  <button
                    class="class-detail-pane__property-name"
                    onClick={() => onPropertySelect(prop.id)}
                  >
                    {prop.label}
                  </button>
                  <span class="class-detail-pane__datatype">
                    {ontologyClasses.value.find((c) => c.uri === prop.domain_class_uris[0])?.label ?? prop.domain_class_uris[0]}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div class="class-detail-pane__footer">
        <button
          class={`class-detail-pane__history-toggle ${historyExpanded ? "class-detail-pane__history-toggle--expanded" : ""}`}
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
              onMouseDown={onResizeStart}
            />
            <div class="class-detail-pane__section-scroll">
              <HistoryPanel source={{ type: "project", id: projectId }} refreshKey={historyVersion.value} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
