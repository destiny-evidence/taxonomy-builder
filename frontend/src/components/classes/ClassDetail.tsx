import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { classesApi } from "../../api/classes";
import { ApiError } from "../../api/client";
import type { OntologyClass, OntologyClassCreate } from "../../types/models";
import { toCamelCase, validateIdentifier } from "../../utils/strings";
import { formatDatetime } from "../../utils/dates";
import "../common/WorkspaceDetail.css";

interface ViewEditProps {
  mode?: "view";
  ontologyClass: OntologyClass;
  onRefresh: () => void;
  onDeleted: () => void;
}

interface CreateProps {
  mode: "create";
  projectId: string;
  onSuccess: () => void;
  onCancel: () => void;
  onRefresh: () => void;
}

type ClassDetailProps = ViewEditProps | CreateProps;

interface EditDraft {
  label: string;
  identifier: string;
  description: string;
  scope_note: string;
}

export function ClassDetail(props: ClassDetailProps) {
  const isCreateMode = props.mode === "create";
  const ontologyClass = isCreateMode ? null : props.ontologyClass;

  const [isEditing, setIsEditing] = useState(isCreateMode);
  const [editDraft, setEditDraft] = useState<EditDraft | null>(
    isCreateMode
      ? { label: "", identifier: "", description: "", scope_note: "" }
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
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    if (!isCreateMode) {
      setIsEditing(false);
      setEditDraft(null);
      setValidationErrors({});
      setSaveError(null);
    }
  }, [isCreateMode, ontologyClass?.id]);

  useEffect(() => {
    if (isCreateMode && !identifierTouched && editDraft?.label) {
      setEditDraft((prev) => prev ? { ...prev, identifier: toCamelCase(prev.label) } : prev);
    }
  }, [isCreateMode, editDraft?.label, identifierTouched]);

  function handleEditClick() {
    if (!ontologyClass) return;
    const draft: EditDraft = {
      label: ontologyClass.label,
      identifier: ontologyClass.identifier,
      description: ontologyClass.description ?? "",
      scope_note: ontologyClass.scope_note ?? "",
    };
    setEditDraft(draft);
    setInitialDraft(draft);
    setValidationErrors({});
    setDeleteError(null);
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
        const data: OntologyClassCreate = {
          label: editDraft.label.trim(),
          identifier: editDraft.identifier.trim(),
          description: editDraft.description.trim() || undefined,
          scope_note: editDraft.scope_note.trim() || undefined,
        };
        await classesApi.create((props as CreateProps).projectId, data);
        (props as CreateProps).onSuccess();
      } else {
        await classesApi.update(ontologyClass!.id, {
          label: editDraft.label,
          description: editDraft.description || null,
          scope_note: editDraft.scope_note || null,
        });
        setEditDraft(null);
        setIsEditing(false);
        props.onRefresh();
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSaveError("A class with this identifier already exists");
      } else {
        setSaveError(err instanceof Error ? err.message : isCreateMode ? "Failed to create class" : "Failed to save class");
      }
    } finally {
      setSaveLoading(false);
    }
  }

  function updateDraft<K extends keyof EditDraft>(field: K, value: EditDraft[K]) {
    if (!editDraft) return;
    setFormTouched(true);
    setEditDraft({ ...editDraft, [field]: value });

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
    return missing;
  }

  async function handleDelete() {
    if (!ontologyClass) return;
    setDeleteLoading(true);
    setDeleteError(null);
    try {
      await classesApi.delete(ontologyClass.id);
      props.onRefresh();
      (props as ViewEditProps).onDeleted();
    } catch (err) {
      setShowDeleteConfirm(false);
      if (err instanceof ApiError && err.status === 409) {
        setDeleteError("Cannot delete this class because it is referenced by one or more properties");
      } else {
        setDeleteError(err instanceof Error ? err.message : "Failed to delete class");
      }
    } finally {
      setDeleteLoading(false);
    }
  }

  const title = isCreateMode ? "New Class" : isEditing ? "Edit Class" : ontologyClass!.label;

  return (
    <div class="workspace-detail">
      <div class="workspace-detail__header">
        <h3 class="workspace-detail__title">{title}</h3>
        {!isCreateMode && !isEditing && (
          <div class="workspace-detail__header-actions">
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
          </div>
        )}
      </div>

      {(saveError || deleteError) && (
        <div class="workspace-detail__error" role="alert">
          {saveError || deleteError}
        </div>
      )}

      <div class="workspace-detail__content">
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
              />
            ) : (
              <div class="workspace-detail__field">
                <label class="workspace-detail__label">Identifier</label>
                <div class="workspace-detail__value workspace-detail__value--mono">
                  {ontologyClass!.identifier}
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

            <Input
              label="Scope Note"
              name="scope_note"
              value={editDraft.scope_note}
              onChange={(value) => updateDraft("scope_note", value)}
              multiline
            />
          </>
        ) : ontologyClass ? (
          <>
            <div class="workspace-detail__field">
              <label class="workspace-detail__label">Identifier</label>
              <div class="workspace-detail__value workspace-detail__value--mono">
                {ontologyClass.identifier}
              </div>
            </div>

            {ontologyClass.description && (
              <div class="workspace-detail__field">
                <label class="workspace-detail__label">Description</label>
                <div class="workspace-detail__value">
                  {ontologyClass.description}
                </div>
              </div>
            )}

            {ontologyClass.scope_note && (
              <div class="workspace-detail__field">
                <label class="workspace-detail__label">Scope Note</label>
                <div class="workspace-detail__value">
                  {ontologyClass.scope_note}
                </div>
              </div>
            )}

            <div class="workspace-detail__meta">
              <span>Created {formatDatetime(ontologyClass.created_at)}</span>
              <span>Updated {formatDatetime(ontologyClass.updated_at)}</span>
            </div>
          </>
        ) : null}
      </div>

      {isEditing &&
        formTouched &&
        !saveLoading &&
        !isFormValid &&
        getMissingFields().length > 0 && (
          <div class="workspace-detail__missing" aria-live="polite">
            Still needed: {getMissingFields().join(", ")}
          </div>
        )}

      {isEditing &&
        !isCreateMode &&
        !saveLoading &&
        isFormValid &&
        !hasChanges && (
          <div class="workspace-detail__hint" aria-live="polite">
            No changes to save
          </div>
        )}

      {isEditing && (
        <div class="workspace-detail__actions">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCancel}
            disabled={saveLoading}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={
              hasValidationErrors ||
              !isFormValid ||
              (!isCreateMode && !hasChanges) ||
              saveLoading
            }
          >
            {isCreateMode
              ? saveLoading
                ? "Creating..."
                : "Create Class"
              : saveLoading
                ? "Saving..."
                : "Save"}
          </Button>
        </div>
      )}

      {!isCreateMode && ontologyClass && (
        <ConfirmDialog
          isOpen={showDeleteConfirm}
          title="Delete Class"
          message={`Are you sure you want to delete "${ontologyClass.label}"?`}
          confirmLabel={deleteLoading ? "Deleting..." : "Confirm"}
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
        />
      )}
    </div>
  );
}
