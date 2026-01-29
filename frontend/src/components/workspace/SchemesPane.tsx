import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { currentProject } from "../../state/projects";
import { schemes } from "../../state/schemes";
import { schemesApi } from "../../api/schemes";
import { ApiError } from "../../api/client";
import "./SchemesPane.css";

interface SchemesPaneProps {
  projectId: string;
  currentSchemeId: string | null;
  onSchemeSelect: (schemeId: string) => void;
  onNewScheme: () => void;
  onImport: () => void;
}

interface EditDraft {
  title: string;
  uri: string;
  description: string;
  publisher: string;
  version: string;
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

export function SchemesPane({
  projectId,
  currentSchemeId,
  onSchemeSelect,
  onNewScheme,
  onImport,
}: SchemesPaneProps) {
  const projectSchemes = schemes.value.filter((s) => s.project_id === projectId);
  const project = currentProject.value;
  const selectedScheme = currentSchemeId
    ? schemes.value.find((s) => s.id === currentSchemeId)
    : null;

  const [isEditing, setIsEditing] = useState(false);
  const [editDraft, setEditDraft] = useState<EditDraft | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Partial<Record<keyof EditDraft, string>>>({});

  // Exit edit mode when scheme changes (user selected different scheme)
  useEffect(() => {
    setIsEditing(false);
    setEditDraft(null);
    setError(null);
    setValidationErrors({});
  }, [currentSchemeId]);

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
  const displayValues = editDraft ?? (selectedScheme ? {
    title: selectedScheme.title,
    uri: selectedScheme.uri ?? "",
    description: selectedScheme.description ?? "",
    publisher: selectedScheme.publisher ?? "",
    version: selectedScheme.version ?? "",
  } : null);

  function handleEditClick() {
    if (!selectedScheme) return;
    setEditDraft({
      title: selectedScheme.title,
      uri: selectedScheme.uri ?? "",
      description: selectedScheme.description ?? "",
      publisher: selectedScheme.publisher ?? "",
      version: selectedScheme.version ?? "",
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
    if (!editDraft || !selectedScheme) return;

    setLoading(true);
    setError(null);

    const data = {
      title: editDraft.title,
      uri: editDraft.uri || null,
      description: editDraft.description || null,
      publisher: editDraft.publisher || null,
      version: editDraft.version || null,
    };

    try {
      const updatedScheme = await schemesApi.update(selectedScheme.id, data);
      // Update the schemes signal with the updated scheme
      schemes.value = schemes.value.map((s) =>
        s.id === selectedScheme.id ? updatedScheme : s
      );
      setEditDraft(null);
      setIsEditing(false);
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
    <div class="schemes-pane">
      <div class="schemes-pane__header">
        <a href="/projects" class="schemes-pane__back-link">
          Projects
        </a>
        <h2 class="schemes-pane__project-title">{project?.name}</h2>
      </div>

      <div class="schemes-pane__content">
        {projectSchemes.length === 0 ? (
          <div class="schemes-pane__empty">No schemes in this project</div>
        ) : (
          <div class="schemes-pane__list">
            {projectSchemes.map((scheme) => (
              <button
                key={scheme.id}
                class={`schemes-pane__item ${
                  scheme.id === currentSchemeId ? "schemes-pane__item--selected" : ""
                }`}
                onClick={() => onSchemeSelect(scheme.id)}
              >
                {scheme.title}
              </button>
            ))}
          </div>
        )}

        {selectedScheme && displayValues && (
          <div class={`schemes-pane__detail ${isEditing ? "schemes-pane__detail--editing" : ""}`}>
            <div class="schemes-pane__detail-header">
              {isEditing ? (
                <Input
                  label="Title"
                  name="title"
                  value={displayValues.title}
                  onChange={(value) => updateDraft("title", value)}
                  required
                  error={validationErrors.title}
                />
              ) : (
                <h3 class="schemes-pane__detail-title" data-testid="scheme-detail-title">
                  {selectedScheme.title}
                </h3>
              )}
              <div class="schemes-pane__detail-actions">
                {isEditing ? (
                  <>
                    <Button variant="secondary" onClick={handleCancel} disabled={loading}>
                      Cancel
                    </Button>
                    <Button variant="primary" onClick={handleSave} disabled={loading || hasValidationErrors}>
                      {loading ? "Saving..." : "Save"}
                    </Button>
                  </>
                ) : (
                  <Button variant="secondary" onClick={handleEditClick}>
                    Edit
                  </Button>
                )}
              </div>
            </div>

            {error && isEditing && (
              <div class="schemes-pane__detail-error">{error}</div>
            )}

            <div class="schemes-pane__detail-content">
              {isEditing ? (
                <>
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
                  <Input
                    label="Version"
                    name="version"
                    value={displayValues.version}
                    onChange={(value) => updateDraft("version", value)}
                    placeholder="e.g., 1.0.0"
                  />
                </>
              ) : (
                <>
                  <div class="schemes-pane__detail-field">
                    <label class="schemes-pane__detail-label">URI</label>
                    <div class="schemes-pane__detail-value">
                      {selectedScheme.uri || <span class="schemes-pane__detail-empty">Not set</span>}
                    </div>
                  </div>

                  <div class="schemes-pane__detail-field">
                    <label class="schemes-pane__detail-label">Description</label>
                    <div class="schemes-pane__detail-value">
                      {selectedScheme.description || <span class="schemes-pane__detail-empty">Not set</span>}
                    </div>
                  </div>

                  <div class="schemes-pane__detail-field">
                    <label class="schemes-pane__detail-label">Publisher</label>
                    <div class="schemes-pane__detail-value">
                      {selectedScheme.publisher || <span class="schemes-pane__detail-empty">Not set</span>}
                    </div>
                  </div>

                  <div class="schemes-pane__detail-field">
                    <label class="schemes-pane__detail-label">Version</label>
                    <div class="schemes-pane__detail-value">
                      {selectedScheme.version || <span class="schemes-pane__detail-empty">Not set</span>}
                    </div>
                  </div>

                  <div class="schemes-pane__detail-field">
                    <label class="schemes-pane__detail-label">Created</label>
                    <div class="schemes-pane__detail-value">
                      {formatDate(selectedScheme.created_at)}
                    </div>
                  </div>

                  <div class="schemes-pane__detail-field">
                    <label class="schemes-pane__detail-label">Updated</label>
                    <div class="schemes-pane__detail-value">
                      {formatDate(selectedScheme.updated_at)}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      <div class="schemes-pane__footer">
        <Button variant="secondary" onClick={onNewScheme}>
          + New Scheme
        </Button>
        <Button variant="secondary" onClick={onImport}>
          Import
        </Button>
      </div>
    </div>
  );
}
