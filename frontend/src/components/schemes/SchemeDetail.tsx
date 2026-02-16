import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { schemesApi } from "../../api/schemes";
import { ApiError } from "../../api/client";
import { schemes, currentScheme } from "../../state/schemes";
import type { ConceptScheme } from "../../types/models";
import "./SchemeDetail.css";

interface SchemeDetailProps {
  scheme: ConceptScheme;
  onRefresh: () => void;
}

interface EditDraft {
  title: string;
  uri: string;
  description: string;
  publisher: string;
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

export function SchemeDetail({ scheme, onRefresh }: SchemeDetailProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editDraft, setEditDraft] = useState<EditDraft | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Partial<Record<keyof EditDraft, string>>>({});

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
    publisher: scheme.publisher ?? "",
  };

  function handleEditClick() {
    setEditDraft({
      title: scheme.title,
      uri: scheme.uri ?? "",
      description: scheme.description ?? "",
      publisher: scheme.publisher ?? "",
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
      publisher: editDraft.publisher || null,
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
            <Input
              label="Publisher"
              name="publisher"
              value={displayValues.publisher}
              onChange={(value) => updateDraft("publisher", value)}
              placeholder="Organization or person"
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

            {scheme.publisher && (
              <div class="scheme-detail__field">
                <label class="scheme-detail__label">Publisher</label>
                <div class="scheme-detail__value">{scheme.publisher}</div>
              </div>
            )}

            <div class="scheme-detail__meta">
              <span class="scheme-detail__meta-item">
                Created {formatDate(scheme.created_at)}
              </span>
              <span class="scheme-detail__meta-separator">•</span>
              <span class="scheme-detail__meta-item">
                Updated {formatDate(scheme.updated_at)}
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
            </div>
          </>
        )}
      </div>
    </div>
  );
}
