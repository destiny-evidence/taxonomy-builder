import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { propertiesApi } from "../../api/properties";
import { ApiError } from "../../api/client";
import { ontologyClasses } from "../../state/ontology";
import { schemes } from "../../state/schemes";
import { DATATYPE_LABELS } from "../../types/models";
import type { Property, PropertyCreate } from "../../types/models";
import { toCamelCase, validateIdentifier } from "../../utils/strings";
import "./PropertyDetail.css";

interface ViewEditProps {
  mode?: "view";
  property: Property;
  onRefresh: () => void;
  onClose: () => void;
}

interface CreateProps {
  mode: "create";
  projectId: string;
  domainClassUri?: string;
  onSuccess: () => void;
  onCancel: () => void;
  onRefresh: () => void;
}

type PropertyDetailProps = ViewEditProps | CreateProps;

interface EditDraft {
  label: string;
  identifier: string;
  description: string;
  domain_class: string;
  range_type: "scheme" | "datatype" | "class";
  range_scheme_id: string;
  range_datatype: string;
  range_class: string;
  cardinality: "single" | "multiple";
  required: boolean;
}


function extractLocalName(uri: string): string {
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

export function PropertyDetail(props: PropertyDetailProps) {
  const isCreateMode = props.mode === "create";
  const property = isCreateMode ? null : props.property;

  const [isEditing, setIsEditing] = useState(isCreateMode);
  const [editDraft, setEditDraft] = useState<EditDraft | null>(
    isCreateMode
      ? {
          label: "",
          identifier: "",
          description: "",
          domain_class: (props as CreateProps).domainClassUri ?? "",
          range_type: "datatype",
          range_scheme_id: "",
          range_datatype: "",
          range_class: "",
          cardinality: "single",
          required: false,
        }
      : null,
  );
  const [initialDraft, setInitialDraft] = useState<EditDraft | null>(editDraft);
  const [identifierTouched, setIdentifierTouched] = useState(false);
  const [formTouched, setFormTouched] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Partial<Record<string, string>>>({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Exit edit mode when property changes (view/edit mode only)
  useEffect(() => {
    if (!isCreateMode) {
      setIsEditing(false);
      setEditDraft(null);
      setValidationErrors({});
      setSaveError(null);
    }
  }, [isCreateMode, property?.id]);

  // Auto-generate identifier from label in create mode
  useEffect(() => {
    if (isCreateMode && !identifierTouched && editDraft?.label) {
      setEditDraft((prev) => prev ? { ...prev, identifier: toCamelCase(prev.label) } : prev);
    }
  }, [isCreateMode, editDraft?.label, identifierTouched]);

  const classes = ontologyClasses.value;
  const projectSchemes = schemes.value.filter((s) =>
    isCreateMode ? s.project_id === (props as CreateProps).projectId : s.project_id === property!.project_id,
  );

  function handleEditClick() {
    if (!property) return;
    const draft: EditDraft = {
      label: property.label,
      identifier: property.identifier,
      description: property.description ?? "",
      domain_class: property.domain_class,
      range_type: property.range_scheme_id ? "scheme" : property.range_class ? "class" : "datatype",
      range_scheme_id: property.range_scheme_id ?? "",
      range_datatype: property.range_datatype ?? "",
      range_class: property.range_class ?? "",
      cardinality: property.cardinality,
      required: property.required,
    };
    setEditDraft(draft);
    setInitialDraft(draft);
    setValidationErrors({});
    setIsEditing(true);
  }

  function handleCancel() {
    if (isCreateMode) {
      (props as CreateProps).onCancel();
      return;
    }
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
      if (isCreateMode) {
        const data: PropertyCreate = {
          label: editDraft.label.trim(),
          identifier: editDraft.identifier.trim(),
          description: editDraft.description.trim() || undefined,
          domain_class: editDraft.domain_class,
          range_scheme_id: editDraft.range_type === "scheme" ? editDraft.range_scheme_id || undefined : undefined,
          range_datatype: editDraft.range_type === "datatype" ? editDraft.range_datatype || undefined : undefined,
          range_class: editDraft.range_type === "class" ? editDraft.range_class || undefined : undefined,
          cardinality: editDraft.cardinality,
          required: editDraft.required,
        };
        await propertiesApi.create((props as CreateProps).projectId, data);
        (props as CreateProps).onSuccess();
      } else {
        await propertiesApi.update(property!.id, {
          label: editDraft.label,
          description: editDraft.description || null,
          domain_class: editDraft.domain_class,
          range_scheme_id: editDraft.range_type === "scheme" ? editDraft.range_scheme_id || null : null,
          range_datatype: editDraft.range_type === "datatype" ? editDraft.range_datatype || null : null,
          range_class: editDraft.range_type === "class" ? editDraft.range_class || null : null,
          cardinality: editDraft.cardinality,
          required: editDraft.required,
        });
        setEditDraft(null);
        setIsEditing(false);
        props.onRefresh();
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSaveError("A property with this identifier already exists");
      } else {
        setSaveError(err instanceof Error ? err.message : isCreateMode ? "Failed to create property" : "Failed to save property");
      }
    } finally {
      setSaveLoading(false);
    }
  }

  function updateDraft<K extends keyof EditDraft>(field: K, value: EditDraft[K]) {
    if (!editDraft) return;
    setFormTouched(true);
    setEditDraft({ ...editDraft, [field]: value });

    // Validate the field
    let error: string | null = null;
    if (field === "label" && !(value as string).trim()) {
      error = "Label is required";
    }
    if (field === "identifier" && isCreateMode) {
      error = validateIdentifier(value as string);
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

  function handleIdentifierChange(value: string) {
    setIdentifierTouched(true);
    updateDraft("identifier", value);
  }

  const identifierError = isCreateMode && editDraft?.identifier ? validateIdentifier(editDraft.identifier) : null;

  const hasValidationErrors = Object.keys(validationErrors).length > 0;

  const isFormValid = editDraft
    ? !!editDraft.label.trim() &&
      !!editDraft.domain_class &&
      (editDraft.range_type === "scheme"
        ? !!editDraft.range_scheme_id
        : editDraft.range_type === "class"
          ? !!editDraft.range_class
          : !!editDraft.range_datatype) &&
      (isCreateMode ? !!editDraft.identifier.trim() && !identifierError : true)
    : false;

  const hasChanges = isCreateMode
    ? true
    : editDraft && initialDraft
      ? JSON.stringify(editDraft) !== JSON.stringify(initialDraft)
      : false;

  function getMissingFields(): string[] {
    if (!editDraft) return [];
    const missing: string[] = [];
    if (!editDraft.label.trim()) missing.push("Label");
    if (isCreateMode && !editDraft.identifier.trim()) missing.push("Identifier");
    else if (isCreateMode && identifierError) missing.push("Valid identifier");
    if (!editDraft.domain_class) missing.push("Class");
    if (editDraft.range_type === "scheme" && !editDraft.range_scheme_id) missing.push("Range scheme");
    if (editDraft.range_type === "datatype" && !editDraft.range_datatype) missing.push("Range datatype");
    if (editDraft.range_type === "class" && !editDraft.range_class) missing.push("Range class");
    return missing;
  }

  async function handleDelete() {
    if (!property) return;
    setDeleteLoading(true);
    try {
      await propertiesApi.delete(property.id);
      props.onRefresh();
      (props as ViewEditProps).onClose();
    } catch (err) {
      console.error("Failed to delete property:", err);
    } finally {
      setDeleteLoading(false);
      setShowDeleteConfirm(false);
    }
  }

  const title = isCreateMode ? "New Property" : isEditing ? "Edit Property" : property!.label;

  return (
    <div class="property-detail">
      <div class="property-detail__header">
        <h3 class="property-detail__title">{title}</h3>
        {!isCreateMode && !isEditing && (
          <div class="property-detail__header-actions">
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
            <Button variant="ghost" size="sm" onClick={(props as ViewEditProps).onClose} aria-label="Close">
              ×
            </Button>
          </div>
        )}
        {!isCreateMode && isEditing && (
          <Button variant="ghost" size="sm" onClick={(props as ViewEditProps).onClose} aria-label="Close">
            ×
          </Button>
        )}
      </div>

      {saveError && (
        <div class="property-detail__error" role="alert">{saveError}</div>
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
            />

            {isCreateMode ? (
              <Input
                label="Identifier"
                name="identifier"
                value={editDraft.identifier}
                onChange={handleIdentifierChange}
                required
                error={identifierError ?? undefined}
                placeholder="e.g., dateOfBirth"
              />
            ) : (
              <div class="property-detail__field">
                <label class="property-detail__label">Identifier</label>
                <div class="property-detail__value property-detail__value--mono">
                  {property!.identifier}
                </div>
              </div>
            )}

            <Input
              label="Description"
              name="description"
              value={editDraft.description}
              onChange={(value) => updateDraft("description", value)}
              multiline
            />

            <div class="property-detail__field">
              <label class="property-detail__label">Class</label>
              <div class="property-detail__value">
                {classes.find((c) => c.uri === editDraft.domain_class)?.label ?? extractLocalName(editDraft.domain_class)}
              </div>
            </div>

            <fieldset class="property-detail__fieldset">
              <legend class="property-detail__legend">Range Type</legend>
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
                <label class="property-detail__radio">
                  <input
                    type="radio"
                    name="rangeType"
                    value="class"
                    checked={editDraft.range_type === "class"}
                    onChange={() => updateDraft("range_type", "class")}
                  />
                  <span>Class</span>
                </label>
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
              ) : editDraft.range_type === "class" ? (
                <div class="property-detail__field">
                  <label class="property-detail__label" htmlFor="edit-range-class">
                    Range Class
                  </label>
                  <select
                    id="edit-range-class"
                    class="property-detail__select"
                    value={editDraft.range_class}
                    onChange={(e) => updateDraft("range_class", (e.target as HTMLSelectElement).value)}
                  >
                    <option value="">Select a class...</option>
                    {classes.map((cls) => (
                      <option key={cls.uri} value={cls.uri}>
                        {cls.label}
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
                    {Object.entries(DATATYPE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </fieldset>

            <fieldset class="property-detail__fieldset">
              <legend class="property-detail__legend">Cardinality</legend>
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
            </fieldset>

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
        ) : property ? (
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
              <label class="property-detail__label">Class</label>
              <div class="property-detail__value">
                {classes.find((c) => c.uri === property.domain_class)?.label ?? extractLocalName(property.domain_class)}
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
        ) : null}
      </div>

      {isEditing && formTouched && !saveLoading && !isFormValid && getMissingFields().length > 0 && (
        <div class="property-detail__missing" aria-live="polite">
          Still needed: {getMissingFields().join(", ")}
        </div>
      )}

      {isEditing && !isCreateMode && !saveLoading && isFormValid && !hasChanges && (
        <div class="property-detail__hint" aria-live="polite">No changes to save</div>
      )}

      {isEditing && (
        <div class="property-detail__actions">
          <Button variant="secondary" size="sm" onClick={handleCancel} disabled={saveLoading}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={hasValidationErrors || !isFormValid || (!isCreateMode && !hasChanges) || saveLoading}
          >
            {isCreateMode
              ? saveLoading ? "Creating..." : "Create Property"
              : saveLoading ? "Saving..." : "Save"}
          </Button>
        </div>
      )}

      {!isCreateMode && property && (
        <ConfirmDialog
          isOpen={showDeleteConfirm}
          title="Delete Property"
          message={`Are you sure you want to delete "${property.label}"?`}
          confirmLabel={deleteLoading ? "Deleting..." : "Confirm"}
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
        />
      )}
    </div>
  );
}
