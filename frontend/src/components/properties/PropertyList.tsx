import { properties, propertiesLoading, propertiesError } from "../../state/properties";
import { Button } from "../common/Button";
import "./PropertyList.css";

interface PropertyListProps {
  onSelect: (propertyId: string) => void;
  onNew: () => void;
}

export function PropertyList({ onSelect, onNew }: PropertyListProps) {
  if (propertiesLoading.value) {
    return <div class="property-list__loading">Loading properties...</div>;
  }

  if (propertiesError.value) {
    return <div class="property-list__error">{propertiesError.value}</div>;
  }

  return (
    <div class="property-list">
      {properties.value.length === 0 ? (
        <div class="property-list__empty">No properties defined</div>
      ) : (
        <div class="property-list__items">
          {properties.value.map((property) => (
            <button
              key={property.id}
              class="property-list__item"
              onClick={() => onSelect(property.id)}
            >
              <span class="property-list__label">{property.label}</span>
              <span class="property-list__range">
                {property.range_scheme
                  ? property.range_scheme.title
                  : property.range_datatype}
              </span>
              {property.required && (
                <span class="property-list__required">required</span>
              )}
            </button>
          ))}
        </div>
      )}
      <div class="property-list__footer">
        <Button variant="secondary" size="sm" onClick={onNew}>
          + New Property
        </Button>
      </div>
    </div>
  );
}
