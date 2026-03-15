import { useState, useEffect } from "preact/hooks";
import { Input } from "../common/Input";
import { Button } from "../common/Button";
import { projectsApi } from "../../api/projects";
import { ApiError } from "../../api/client";
import { formatIdentifier } from "../../types/models";
import type { Project } from "../../types/models";
import "./ProjectForm.css";

interface ProjectFormProps {
  project?: Project | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export function ProjectForm({ project, onSuccess, onCancel }: ProjectFormProps) {
  const [name, setName] = useState(project?.name ?? "");
  const [description, setDescription] = useState(project?.description ?? "");
  const [namespace, setNamespace] = useState(project?.namespace ?? "");
  const [identifierPrefix, setIdentifierPrefix] = useState(project?.identifier_prefix ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const prefixLocked = !!project && project.prefix_locked;

  // Sync form state when project prop changes (for edit vs create)
  useEffect(() => {
    setName(project?.name ?? "");
    setDescription(project?.description ?? "");
    setNamespace(project?.namespace ?? "");
    setIdentifierPrefix(project?.identifier_prefix ?? "");
    setError(null);
  }, [project]);

  function handlePrefixChange(value: string) {
    setIdentifierPrefix(value.replace(/[^A-Za-z]/g, "").toUpperCase().slice(0, 4));
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (project) {
        await projectsApi.update(project.id, {
          name,
          description: description || null,
          namespace,
          identifier_prefix: identifierPrefix,
        });
      } else {
        await projectsApi.create({
          name,
          description: description || null,
          namespace,
          identifier_prefix: identifierPrefix,
        });
      }
      onSuccess();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "An error occurred");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form class="project-form" onSubmit={handleSubmit}>
      {error && <div class="project-form__error">{error}</div>}

      <Input
        label="Name"
        name="name"
        value={name}
        placeholder="Enter project name"
        required
        onChange={setName}
      />

      <Input
        label="Description"
        name="description"
        value={description}
        placeholder="Optional description"
        multiline
        onChange={setDescription}
      />

      <Input
        label="Namespace"
        name="namespace"
        type="url"
        value={namespace}
        placeholder="https://example.org/vocab"
        required
        onChange={setNamespace}
      />

      {prefixLocked ? (
        <div class="project-form__field">
          <label class="project-form__label">Identifier Prefix</label>
          <div class="project-form__prefix-locked">
            <code class="project-form__prefix-badge">{identifierPrefix}</code>
            <span class="project-form__prefix-locked-text">
              Locked — identifiers in use
            </span>
          </div>
        </div>
      ) : (
        <div class="project-form__field">
          <Input
            label="Identifier Prefix"
            name="identifier_prefix"
            value={identifierPrefix}
            placeholder="e.g. EVD"
            required
            maxLength={4}
            onChange={handlePrefixChange}
          />
          <span class="project-form__help">
            1-4 uppercase letters. Generates identifiers like {formatIdentifier(identifierPrefix || "EVD", 1)}. Cannot be changed once concepts are created.
          </span>
        </div>
      )}

      <div class="project-form__actions">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading || !name.trim() || !namespace.trim() || (!prefixLocked && !identifierPrefix.trim())}>
          {loading ? "Saving..." : project ? "Save Changes" : "Create Project"}
        </Button>
      </div>
    </form>
  );
}
