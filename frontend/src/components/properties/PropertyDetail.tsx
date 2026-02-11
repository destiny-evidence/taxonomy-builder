import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { propertiesApi } from "../../api/properties";
import { ontologyClasses } from "../../state/ontology";
import { schemes } from "../../state/schemes";
import type { Property } from "../../types/models";
import "./PropertyDetail.css";

interface PropertyDetailProps {
  property: Property;
  onRefresh: () => void;
  onClose: () => void;
}

interface EditDraft {
  label: string;
  description: string;
  domain_class: string;
  range_type: "scheme" | "datatype";
  range_scheme_id: string;
  range_datatype: string;
  cardinality: "single" | "multiple";
  required: boolean;
}

const ALLOWED_DATATYPES = [
  "xsd:string",
  "xsd:integer",
  "xsd:decimal",
  "xsd:boolean",
  "xsd:date",
  "xsd:dateTime",
  "xsd:anyURI",
];

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
  const [isEditing, setIsEditing] = useState(false);
  const [editDraft, setEditDraft] = useState<EditDraft | null>(null);
  const [validationErrors, setValidationErrors] = useState<Partial<Record<string, string>>>({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Exit edit mode when property changes
  useEffect(() => {
    setIsEditing(false);
    setEditDraft(null);
    setValidationErrors({});
    setSaveError(null);
  }, [property.id]);

  const classes = ontologyClasses.value;
  const projectSchemes = schemes.value.filter((s) => s.project_id === property.project_id);

  function handleEditClick() {
    setEditDraft({
      label: property.label,
      description: property.description ?? "",
      domain_class: property.domain_class,
      range_type: property.range_scheme_id ? "scheme" : "datatype",
      range_scheme_id: property.range_scheme_id ?? "",
      range_datatype: property.range_datatype ?? "",
      cardinality: property.cardinality,
      required: property.required,
    });
    setValidationErrors({});
    setIsEditing(true);
  }

  function handleCancel() {
    setEditDraft(null);
    setValidationErrors({});
    setSaveError(null);
    setIsEditing(false);
  }

  async function handleSave() {
    if (!editDraft) return;

    setSaveLoading(true);
    setSaveError(null);

    try {
      await propertiesApi.update(property.id, {
        label: editDraft.label,
        description: editDraft.description || null,
        domain_class: editDraft.domain_class,
        range_scheme_id: editDraft.range_type === "scheme" ? editDraft.range_scheme_id : null,
        range_datatype: editDraft.range_type === "datatype" ? editDraft.range_datatype : null,
        cardinality: editDraft.cardinality,
        required: editDraft.required,
      });
      setEditDraft(null);
      setIsEditing(false);
      onRefresh();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save property");
    } finally {
      setSaveLoading(false);
    }
  }

  function updateDraft<K extends keyof EditDraft>(field: K, value: EditDraft[K]) {
    if (!editDraft) return;
    setEditDraft({ ...editDraft, [field]: value });

    // Validate the field
    let error: string | null = null;
    if (field === "label" && !(value as string).trim()) {
      error = "Label is required";
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

      {saveError && (
        <div class="property-detail__error">{saveError}</div>
      )}

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

            <div class="property-detail__field">
              <label class="property-detail__label">Identifier</label>
              <div class="property-detail__value property-detail__value--mono">
                {property.identifier}
              </div>
            </div>

            <Input
              label="Description"
              name="description"
              value={editDraft.description}
              onChange={(value) => updateDraft("description", value)}
              multiline
            />

            <div class="property-detail__field">
              <label class="property-detail__label" htmlFor="edit-domain-class">
                Domain
              </label>
              <select
                id="edit-domain-class"
                class="property-detail__select"
                value={editDraft.domain_class}
                onChange={(e) => updateDraft("domain_class", (e.target as HTMLSelectElement).value)}
              >
                <option value="">Select a class...</option>
                {classes.map((cls) => (
                  <option key={cls.uri} value={cls.uri}>
                    {cls.label}
                  </option>
                ))}
              </select>
            </div>

            <div class="property-detail__field">
              <label class="property-detail__label">Range Type</label>
              <div class="property-detail__radio-group">
                <label class="property-detail__radio">
                  <input
                    type="radio"
                    name="rangeType"
                    value="scheme"
                    checked={editDraft.range_type === "scheme"}
                    onChange={() => updateDraft("range_type", "scheme")}
                  />
                  <span>Scheme</span>
                </label>
                <label class="property-detail__radio">
                  <input
                    type="radio"
                    name="rangeType"
                    value="datatype"
                    checked={editDraft.range_type === "datatype"}
                    onChange={() => updateDraft("range_type", "datatype")}
                  />
                  <span>Datatype</span>
                </label>
              </div>
            </div>

            {editDraft.range_type === "scheme" ? (
              <div class="property-detail__field">
                <label class="property-detail__label" htmlFor="edit-range-scheme">
                  Range Scheme
                </label>
                <select
                  id="edit-range-scheme"
                  class="property-detail__select"
                  value={editDraft.range_scheme_id}
                  onChange={(e) => updateDraft("range_scheme_id", (e.target as HTMLSelectElement).value)}
                >
                  <option value="">Select a scheme...</option>
                  {projectSchemes.map((scheme) => (
                    <option key={scheme.id} value={scheme.id}>
                      {scheme.title}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div class="property-detail__field">
                <label class="property-detail__label" htmlFor="edit-range-datatype">
                  Range Datatype
                </label>
                <select
                  id="edit-range-datatype"
                  class="property-detail__select"
                  value={editDraft.range_datatype}
                  onChange={(e) => updateDraft("range_datatype", (e.target as HTMLSelectElement).value)}
                >
                  <option value="">Select a datatype...</option>
                  {ALLOWED_DATATYPES.map((dt) => (
                    <option key={dt} value={dt}>
                      {dt}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div class="property-detail__field">
              <label class="property-detail__label">Cardinality</label>
              <div class="property-detail__radio-group">
                <label class="property-detail__radio">
                  <input
                    type="radio"
                    name="cardinality"
                    value="single"
                    checked={editDraft.cardinality === "single"}
                    onChange={() => updateDraft("cardinality", "single")}
                  />
                  <span>Single value</span>
                </label>
                <label class="property-detail__radio">
                  <input
                    type="radio"
                    name="cardinality"
                    value="multiple"
                    checked={editDraft.cardinality === "multiple"}
                    onChange={() => updateDraft("cardinality", "multiple")}
                  />
                  <span>Multiple values</span>
                </label>
              </div>
            </div>

            <div class="property-detail__field">
              <label class="property-detail__checkbox">
                <input
                  type="checkbox"
                  checked={editDraft.required}
                  onChange={(e) => updateDraft("required", (e.target as HTMLInputElement).checked)}
                />
                <span>Required</span>
              </label>
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
            <Button variant="secondary" size="sm" onClick={handleCancel} disabled={saveLoading}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSave}
              disabled={hasValidationErrors || isLabelEmpty || saveLoading}
            >
              {saveLoading ? "Saving..." : "Save"}
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
