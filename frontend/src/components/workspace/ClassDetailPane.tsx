import { Button } from "../common/Button";
import { ontologyClasses } from "../../state/ontology";
import { properties, selectedPropertyId } from "../../state/properties";
import "./ClassDetailPane.css";

interface ClassDetailPaneProps {
  classUri: string;
  projectId: string;
  onPropertySelect: (propertyId: string) => void;
  onNewProperty: () => void;
  onSchemeNavigate: (schemeId: string) => void;
}

export function ClassDetailPane({
  classUri,
  projectId: _projectId,
  onPropertySelect,
  onNewProperty,
  onSchemeNavigate,
}: ClassDetailPaneProps) {
  const ontologyClass = ontologyClasses.value.find((c) => c.uri === classUri);
  const classProperties = properties.value.filter((p) => p.domain_class === classUri);

  const classLabel = ontologyClass?.label ?? classUri;
  const classDescription = ontologyClass?.comment;

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
            <Button variant="ghost" size="sm" onClick={onNewProperty}>
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
                        {prop.range_datatype}
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
