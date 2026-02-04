import { useState } from "preact/hooks";
import { Button } from "../common/Button";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { propertiesApi } from "../../api/properties";
import type { Property } from "../../types/models";
import "./PropertyDetail.css";

interface PropertyDetailProps {
  property: Property;
  onRefresh: () => void;
  onClose: () => void;
}

function extractLocalName(uri: string): string {
  // Extract the local part after the last / or #
  const hashIndex = uri.lastIndexOf("#");
  const slashIndex = uri.lastIndexOf("/");
  const index = Math.max(hashIndex, slashIndex);
  return index >= 0 ? uri.substring(index + 1) : uri;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function PropertyDetail({ property, onRefresh, onClose }: PropertyDetailProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  async function handleDelete() {
    setDeleteLoading(true);
    try {
      await propertiesApi.delete(property.id);
      onRefresh();
      onClose();
    } catch (err) {
      console.error("Failed to delete property:", err);
    } finally {
      setDeleteLoading(false);
      setShowDeleteConfirm(false);
    }
  }

  return (
    <div class="property-detail">
      <div class="property-detail__header">
        <h3 class="property-detail__title">{property.label}</h3>
        <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
          ×
        </Button>
      </div>

      <div class="property-detail__content">
        <div class="property-detail__field">
          <label class="property-detail__label">Identifier</label>
          <div class="property-detail__value property-detail__value--mono">
            {property.identifier}
          </div>
        </div>

        {property.description && (
          <div class="property-detail__field">
            <label class="property-detail__label">Description</label>
            <div class="property-detail__value">{property.description}</div>
          </div>
        )}

        <div class="property-detail__field">
          <label class="property-detail__label">Domain</label>
          <div class="property-detail__value">
            {extractLocalName(property.domain_class)}
          </div>
        </div>

        <div class="property-detail__field">
          <label class="property-detail__label">Range</label>
          <div class="property-detail__value">
            {property.range_scheme
              ? property.range_scheme.title
              : property.range_datatype}
          </div>
        </div>

        <div class="property-detail__row">
          <div class="property-detail__field property-detail__field--half">
            <label class="property-detail__label">Cardinality</label>
            <div class="property-detail__value">
              {property.cardinality === "single" ? "Single value" : "Multiple values"}
            </div>
          </div>

          <div class="property-detail__field property-detail__field--half">
            <label class="property-detail__label">Required</label>
            <div class="property-detail__value">
              {property.required ? "Yes" : "No"}
            </div>
          </div>
        </div>

        <div class="property-detail__meta">
          <span>Created {formatDate(property.created_at)}</span>
          <span>Updated {formatDate(property.updated_at)}</span>
        </div>
      </div>

      <div class="property-detail__actions">
        <Button variant="ghost" size="sm" onClick={() => {}}>
          Edit
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowDeleteConfirm(true)}
        >
          Delete
        </Button>
      </div>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete Property"
        message={`Are you sure you want to delete "${property.label}"?`}
        confirmLabel={deleteLoading ? "Deleting..." : "Confirm"}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
