import { PropertyDetail } from "../properties/PropertyDetail";
import { SchemePreview } from "../properties/SchemePreview";
import { selectedProperty, selectedPropertyId, creatingProperty } from "../../state/properties";
import { datatypeLabel } from "../../types/models";
import "./PropertyPane.css";

interface PropertyPaneProps {
  onDelete: () => void;
  onRefresh: () => void;
  onSchemeNavigate: (schemeId: string) => void;
}

export function PropertyPane({ onDelete: _onDelete, onRefresh, onSchemeNavigate }: PropertyPaneProps) {
  const creating = creatingProperty.value;
  const property = selectedProperty.value;

  function handleClose() {
    selectedPropertyId.value = null;
  }

  function handleCreateSuccess() {
    creatingProperty.value = null;
    onRefresh();
  }

  function handleCreateCancel() {
    creatingProperty.value = null;
  }

  if (creating) {
    return (
      <div class="property-pane">
        <PropertyDetail
          key="create"
          mode="create"
          projectId={creating.projectId}
          domainClassUri={creating.domainClassUri}
          onSuccess={handleCreateSuccess}
          onCancel={handleCreateCancel}
          onRefresh={onRefresh}
        />
      </div>
    );
  }

  if (!property) {
    return (
      <div class="property-pane">
        <div class="property-pane__empty">Select a property to view details</div>
      </div>
    );
  }

  return (
    <div class="property-pane">
      <PropertyDetail
        key={property.id}
        property={property}
        onRefresh={onRefresh}
        onClose={handleClose}
      />

      {/* Values section - shows what values this property can have */}
      <div class="property-pane__values">
        {property.range_datatype ? (
          <span class="property-pane__datatype">{datatypeLabel(property.range_datatype)}</span>
        ) : property.range_scheme ? (
          <>
            <div class="property-pane__scheme-header">
              <span class="property-pane__scheme-name">{property.range_scheme.title}</span>
              <button
                class="property-pane__scheme-link"
                onClick={() => onSchemeNavigate(property.range_scheme!.id)}
              >
                View →
              </button>
            </div>
            <SchemePreview schemeId={property.range_scheme.id} />
          </>
        ) : null}
      </div>
    </div>
  );
}
