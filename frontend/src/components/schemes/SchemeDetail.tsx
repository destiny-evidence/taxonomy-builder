import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { schemesApi } from "../../api/schemes";
import { ApiError } from "../../api/client";
import { schemes, currentScheme } from "../../state/schemes";
import { concepts } from "../../state/concepts";
import type { ConceptScheme } from "../../types/models";
import { formatDatetime } from "../../utils/dates";
import "./SchemeDetail.css";

interface SchemeDetailProps {
  scheme: ConceptScheme;
  onRefresh: () => void;
  onDeleted: () => void;
}

interface EditDraft {
  title: string;
  uri: string;
  description: string;
}

export function SchemeDetail({ scheme, onRefresh, onDeleted }: SchemeDetailProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editDraft, setEditDraft] = useState<EditDraft | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Partial<Record<keyof EditDraft, string>>>({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Exit edit mode when scheme changes
  useEffect(() => {
    setIsEditing(false);
    setEditDraft(null);
    setError(null);
    setValidationErrors({});
  }, [scheme.id]);

  function validateField(field: keyof EditDraft, value: string): string | null {
    if (field === "title") {
      if (!value.trim()) {
        return "Title is required";
      }
    }
    if (field === "uri" && value.trim()) {
      // URI is optional, but if provided, must be valid http/https URL
      try {
        const url = new URL(value);
        if (!url.protocol.match(/^https?:$/)) {
          return "URI must be a valid URL (http or https)";
        }
      } catch {
        return "URI must be a valid URL (http or https)";
      }
    }
    return null;
  }

  const hasValidationErrors = Object.keys(validationErrors).length > 0;

  // Use draft values when editing, otherwise use scheme values
  const displayValues = editDraft ?? {
    title: scheme.title,
    uri: scheme.uri ?? "",
    description: scheme.description ?? "",
  };

  function handleEditClick() {
    setEditDraft({
      title: scheme.title,
      uri: scheme.uri ?? "",
      description: scheme.description ?? "",
    });
    setValidationErrors({});
    setIsEditing(true);
  }

  function handleCancel() {
    setEditDraft(null);
    setError(null);
    setValidationErrors({});
    setIsEditing(false);
  }

  async function handleSave() {
    if (!editDraft) return;

    setLoading(true);
    setError(null);

    const data = {
      title: editDraft.title,
      uri: editDraft.uri || null,
      description: editDraft.description || null,
    };

    try {
      const updatedScheme = await schemesApi.update(scheme.id, data);
      // Update the schemes signal with the updated scheme
      schemes.value = schemes.value.map((s) =>
        s.id === scheme.id ? updatedScheme : s
      );
      // Update currentScheme so TreePane header reflects the changes
      if (currentScheme.value?.id === scheme.id) {
        currentScheme.value = updatedScheme;
      }
      setEditDraft(null);
      setIsEditing(false);
      onRefresh();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "An error occurred");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    setDeleteLoading(true);
    setDeleteError(null);
    try {
      await schemesApi.delete(scheme.id);
      schemes.value = schemes.value.filter((s) => s.id !== scheme.id);
      currentScheme.value = null;
      onDeleted();
    } catch (err) {
      setShowDeleteConfirm(false);
      if (err instanceof ApiError) {
        setDeleteError(err.message);
      } else {
        setDeleteError(err instanceof Error ? err.message : "Failed to delete scheme");
      }
    } finally {
      setDeleteLoading(false);
    }
  }

  function updateDraft(field: keyof EditDraft, value: string) {
    if (!editDraft) return;
    setEditDraft({ ...editDraft, [field]: value });

    // Validate the field
    const error = validateField(field, value);
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

  return (
    <div class="scheme-detail">
      {isEditing && error && (
        <div class="scheme-detail__error">{error}</div>
      )}
      {deleteError && (
        <div class="scheme-detail__error">{deleteError}</div>
      )}

      <div class="scheme-detail__content">
        {isEditing ? (
          <>
            <Input
              label="Title"
              name="title"
              value={displayValues.title}
              onChange={(value) => updateDraft("title", value)}
              required
              error={validationErrors.title}
            />
            <Input
              label="URI"
              name="uri"
              type="url"
              value={displayValues.uri}
              onChange={(value) => updateDraft("uri", value)}
              placeholder="https://example.org/my-scheme"
              error={validationErrors.uri}
            />
            <Input
              label="Description"
              name="description"
              value={displayValues.description}
              onChange={(value) => updateDraft("description", value)}
              placeholder="A description of this concept scheme"
              multiline
            />
            <div class="scheme-detail__actions">
              <Button variant="secondary" size="sm" onClick={handleCancel} disabled={loading}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleSave} disabled={loading || hasValidationErrors}>
                {loading ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </>
        ) : (
          <>
            {scheme.uri && (
              <div class="scheme-detail__field">
                <label class="scheme-detail__label">URI</label>
                <div class="scheme-detail__value">{scheme.uri}</div>
              </div>
            )}

            {scheme.description && (
              <div class="scheme-detail__field">
                <label class="scheme-detail__label">Description</label>
                <div class="scheme-detail__value">{scheme.description}</div>
              </div>
            )}

            <div class="scheme-detail__meta">
              <span class="scheme-detail__meta-item">
                Created {formatDatetime(scheme.created_at)}
              </span>
              <span class="scheme-detail__meta-separator">•</span>
              <span class="scheme-detail__meta-item">
                Updated {formatDatetime(scheme.updated_at)}
              </span>
            </div>

            <div class="scheme-detail__actions-bottom">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleEditClick}
              >
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
          </>
        )}
      </div>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete Scheme"
        message={
          concepts.value.length > 0
            ? `Are you sure you want to delete "${scheme.title}"? This will also delete ${concepts.value.length} concept${concepts.value.length === 1 ? "" : "s"} within it.`
            : `Are you sure you want to delete "${scheme.title}"?`
        }
        confirmLabel={deleteLoading ? "Deleting..." : "Delete"}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
