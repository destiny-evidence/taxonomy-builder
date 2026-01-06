import { useState } from "preact/hooks";
import { Input } from "../common/Input";
import { Button } from "../common/Button";
import { projectsApi } from "../../api/projects";
import { ApiError } from "../../api/client";
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (project) {
        await projectsApi.update(project.id, { name, description: description || null });
      } else {
        await projectsApi.create({ name, description: description || null });
      }
      onSuccess();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("A project with this name already exists.");
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

      <div class="project-form__actions">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading || !name.trim()}>
          {loading ? "Saving..." : project ? "Save Changes" : "Create Project"}
        </Button>
      </div>
    </form>
  );
}
