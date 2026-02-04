import { PropertyDetail } from "../properties/PropertyDetail";
import { selectedProperty, selectedPropertyId } from "../../state/properties";
import "./PropertyPane.css";

interface PropertyPaneProps {
  onDelete: () => void;
  onRefresh: () => void;
  onSchemeNavigate: (schemeId: string) => void;
}

export function PropertyPane({ onDelete: _onDelete, onRefresh, onSchemeNavigate }: PropertyPaneProps) {
  const property = selectedProperty.value;

  function handleClose() {
    selectedPropertyId.value = null;
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
        property={property}
        onRefresh={onRefresh}
        onClose={handleClose}
        onSchemeNavigate={onSchemeNavigate}
      />
    </div>
  );
}
