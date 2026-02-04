import { Button } from "../common/Button";
import type { OntologyClass, Property } from "../../types/models";
import "./ClassCard.css";

interface ClassCardProps {
  ontologyClass: OntologyClass;
  properties: Property[];
  onAddProperty: (classUri: string) => void;
  onPropertyClick: (propertyId: string) => void;
  onSchemeClick: (schemeId: string) => void;
}

export function ClassCard({
  ontologyClass,
  properties,
  onAddProperty,
  onPropertyClick,
  onSchemeClick,
}: ClassCardProps) {
  return (
    <div class="class-card">
      <div class="class-card__header" title={ontologyClass.comment ?? undefined}>
        <h3 class="class-card__title">{ontologyClass.label}</h3>
      </div>

      <div class="class-card__content">
        {properties.length === 0 ? (
          <div class="class-card__empty">No properties defined</div>
        ) : (
          <ul class="class-card__properties">
            {properties.map((prop) => (
              <li key={prop.id} class="class-card__property">
                <button
                  class="class-card__property-name"
                  onClick={() => onPropertyClick(prop.id)}
                >
                  {prop.label}
                </button>
                <span class="class-card__property-range">
                  {prop.range_scheme ? (
                    <button
                      class="class-card__scheme-link"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSchemeClick(prop.range_scheme_id!);
                      }}
                    >
                      {prop.range_scheme.title}
                    </button>
                  ) : (
                    <span class="class-card__datatype">{prop.range_datatype}</span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div class="class-card__footer">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onAddProperty(ontologyClass.uri)}
        >
          + Add Property
        </Button>
      </div>
    </div>
  );
}
