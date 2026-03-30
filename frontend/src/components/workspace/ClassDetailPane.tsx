import { Fragment } from "preact";
import { useState } from "preact/hooks";
import { Button } from "../common/Button";
import { ClassDetail } from "../classes/ClassDetail";
import { HistoryPanel } from "../history/HistoryPanel";
import { useResizeHandle } from "../../hooks/useResizeHandle";
import { ontologyClasses, selectedClassUri, isApplicable } from "../../state/classes";
import { properties, selectedPropertyId, creatingProperty } from "../../state/properties";
import type { Property } from "../../types/models";
import { extractLocalName } from "../../utils/strings";
import { historyVersion } from "../../state/history";
import { datatypeLabel } from "../../types/models";
import "../common/WorkspaceDetail.css";
import "./ClassDetailPane.css";

interface InheritedGroup {
  ancestorUri: string;
  label: string;
  depth: number;
  properties: Property[];
}

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
  const rangeProperties = properties.value.filter(
    (p) => p.range_class === classUri && !p.domain_class_uris.includes(classUri),
  );

  // All applicable properties (direct + inherited via class hierarchy)
  const applicableProperties = properties.value.filter((p) =>
    isApplicable(classUri, p.domain_class_uris)
  );

  // Partition into direct vs inherited
  const directProperties = applicableProperties.filter((p) =>
    p.domain_class_uris.includes(classUri)
  );
  const directIds = new Set(directProperties.map((p) => p.id));

  // BFS to compute depth for each ancestor (nearest parent = 1, grandparent = 2, etc.)
  const ancestorDepth = new Map<string, number>();
  const depthQueue: [string, number][] = (
    ontologyClass?.superclass_uris ?? []
  ).map((uri) => [uri, 1] as [string, number]);
  const depthVisited = new Set<string>();
  while (depthQueue.length > 0) {
    const [uri, depth] = depthQueue.shift()!;
    if (depthVisited.has(uri)) continue;
    depthVisited.add(uri);
    ancestorDepth.set(uri, depth);
    const ancestorClass = ontologyClasses.value.find((c) => c.uri === uri);
    if (ancestorClass) {
      for (const parentUri of ancestorClass.superclass_uris) {
        depthQueue.push([parentUri, depth + 1]);
      }
    }
  }

  // Group inherited properties by nearest contributing ancestor
  const groupMap = new Map<string, InheritedGroup>();

  for (const prop of applicableProperties) {
    if (directIds.has(prop.id)) continue;

    let nearestUri: string | null = null;
    let nearestDepth = Infinity;
    let nearestLabel = "";
    for (const domainUri of prop.domain_class_uris) {
      const depth = ancestorDepth.get(domainUri);
      if (depth === undefined) continue;
      const label = ontologyClasses.value.find((c) => c.uri === domainUri)?.label ?? extractLocalName(domainUri);
      if (depth < nearestDepth || (depth === nearestDepth && label.localeCompare(nearestLabel) < 0)) {
        nearestDepth = depth;
        nearestUri = domainUri;
        nearestLabel = label;
      }
    }

    if (nearestUri) {
      if (!groupMap.has(nearestUri)) {
        const cls = ontologyClasses.value.find((c) => c.uri === nearestUri);
        groupMap.set(nearestUri, {
          ancestorUri: nearestUri,
          label: cls?.label ?? extractLocalName(nearestUri),
          depth: nearestDepth,
          properties: [],
        });
      }
      groupMap.get(nearestUri)!.properties.push(prop);
    }
  }

  const inheritedGroups = [...groupMap.values()].sort((a, b) =>
    a.depth !== b.depth ? a.depth - b.depth : a.label.localeCompare(b.label)
  );

  function handleAddProperty() {
    creatingProperty.value = { projectId, domainClassUri: classUri };
    selectedPropertyId.value = null;
  }

  function renderPropertyRow(prop: Property, inherited: boolean) {
    return (
      <li
        key={prop.id}
        class={`class-detail-pane__property ${
          selectedPropertyId.value === prop.id
            ? "class-detail-pane__property--selected"
            : ""
        } ${inherited ? "class-detail-pane__property--inherited" : ""}`}
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
    );
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
                          class="workspace-detail__link"
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
                          class="workspace-detail__link"
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

        {ontologyClass && ontologyClass.restrictions.length > 0 && (
          <div class="class-detail-pane__section">
            <div class="class-detail-pane__section-header">
              <h3 class="class-detail-pane__section-title">Restrictions</h3>
            </div>
            {ontologyClass.restrictions.map((r) => {
              const propLabel = properties.value.find(
                (p) => p.uri === r.on_property_uri
              )?.label ?? extractLocalName(r.on_property_uri);
              const valueLabel = ontologyClasses.value.find(
                (c) => c.uri === r.value_uri
              )?.label ?? extractLocalName(r.value_uri);

              return (
                <div key={`${r.on_property_uri}-${r.restriction_type}-${r.value_uri}`} class="class-detail-pane__restriction-row">
                  <span class="class-detail-pane__restriction-prop">{propLabel}</span>
                  {" "}
                  <span class="class-detail-pane__restriction-type">{r.restriction_type}</span>
                  {" "}
                  <span class="class-detail-pane__restriction-value">{valueLabel}</span>
                </div>
              );
            })}
          </div>
        )}

        <div class="class-detail-pane__section">
          <div class="class-detail-pane__section-header">
            <h3 class="class-detail-pane__section-title">Properties</h3>
            <Button variant="ghost" size="sm" onClick={handleAddProperty}>
              + Add Property
            </Button>
          </div>

          {directProperties.length === 0 && inheritedGroups.length === 0 && (
            <div class="class-detail-pane__empty">
              No properties defined for this class
            </div>
          )}

          {directProperties.length > 0 && (
            <div class="class-detail-pane__property-group">
              {inheritedGroups.length > 0 && (
                <div class="class-detail-pane__group-header">Direct</div>
              )}
              <ul class="class-detail-pane__property-list">
                {directProperties.map((prop) => renderPropertyRow(prop, false))}
              </ul>
            </div>
          )}

          {inheritedGroups.map((group) => (
            <div key={group.ancestorUri} class="class-detail-pane__property-group">
              <div class="class-detail-pane__group-header class-detail-pane__group-header--inherited">
                Inherited from{" "}
                <button
                  class="workspace-detail__link"
                  onClick={(e) => {
                    e.stopPropagation();
                    selectedClassUri.value = group.ancestorUri;
                  }}
                >
                  {group.label}
                </button>
              </div>
              <ul class="class-detail-pane__property-list">
                {group.properties.map((prop) => renderPropertyRow(prop, true))}
              </ul>
            </div>
          ))}
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
