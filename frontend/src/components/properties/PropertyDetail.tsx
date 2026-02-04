import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { propertiesApi } from "../../api/properties";
import type { Property } from "../../types/models";
import "./PropertyDetail.css";

interface PropertyDetailProps {
  property: Property;
  onRefresh: () => void;
  onClose: () => void;
}

interface EditDraft {
  label: string;
  identifier: string;
  description: string;
}

// Pattern for URI-safe identifiers: alphanumeric, underscores, hyphens, starting with letter
const IDENTIFIER_PATTERN = /^[a-zA-Z][a-zA-Z0-9_-]*$/;

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

function validateIdentifier(value: string): string | null {
  if (!value.trim()) {
    return "Identifier is required";
  }
  if (!value[0].match(/[a-zA-Z]/)) {
    return "Identifier must start with a letter";
  }
  if (!IDENTIFIER_PATTERN.test(value)) {
    return "Identifier must be URI-safe: letters, numbers, underscores, and hyphens only";
  }
  return null;
}

export function PropertyDetail({ property, onRefresh, onClose }: PropertyDetailProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editDraft, setEditDraft] = useState<EditDraft | null>(null);
  const [validationErrors, setValidationErrors] = useState<Partial<Record<keyof EditDraft, string>>>({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Exit edit mode when property changes
  useEffect(() => {
    setIsEditing(false);
    setEditDraft(null);
    setValidationErrors({});
  }, [property.id]);

  function handleEditClick() {
    setEditDraft({
      label: property.label,
      identifier: property.identifier,
      description: property.description ?? "",
    });
    setValidationErrors({});
    setIsEditing(true);
  }

  function handleCancel() {
    setEditDraft(null);
    setValidationErrors({});
    setIsEditing(false);
  }

  function updateDraft(field: keyof EditDraft, value: string) {
    if (!editDraft) return;
    setEditDraft({ ...editDraft, [field]: value });

    // Validate the field
    let error: string | null = null;
    if (field === "label" && !value.trim()) {
      error = "Label is required";
    } else if (field === "identifier") {
      error = validateIdentifier(value);
    }

    setValidationErrors((prev) => {
      const newErrors = { ...prev };
      if (error) {
        newErrors[field] = error;
      } else {
        delete newErrors[field];
      }
      return newErrors;
    });
  }

  const hasValidationErrors = Object.keys(validationErrors).length > 0;
  const isLabelEmpty = !editDraft?.label.trim();

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
        <h3 class="property-detail__title">
          {isEditing ? "Edit Property" : property.label}
        </h3>
        <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
          ×
        </Button>
      </div>

      <div class="property-detail__content">
        {isEditing && editDraft ? (
          <>
            <Input
              label="Label"
              name="label"
              value={editDraft.label}
              onChange={(value) => updateDraft("label", value)}
              required
              error={validationErrors.label}
            />
            <Input
              label="Identifier"
              name="identifier"
              value={editDraft.identifier}
              onChange={(value) => updateDraft("identifier", value)}
              required
              error={validationErrors.identifier}
            />
            <Input
              label="Description"
              name="description"
              value={editDraft.description}
              onChange={(value) => updateDraft("description", value)}
              multiline
            />

            {/* Display non-editable fields for reference */}
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
          </>
        ) : (
          <>
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
          </>
        )}
      </div>

      <div class="property-detail__actions">
        {isEditing ? (
          <>
            <Button variant="secondary" size="sm" onClick={handleCancel}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={hasValidationErrors || isLabelEmpty}
            >
              Save
            </Button>
          </>
        ) : (
          <>
            <Button variant="ghost" size="sm" onClick={handleEditClick}>
              Edit
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDeleteConfirm(true)}
            >
              Delete
            </Button>
          </>
        )}
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
