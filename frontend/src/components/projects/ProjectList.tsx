import { useState } from "preact/hooks";
import { projects, projectsLoading, projectsError } from "../../state/projects";
import { projectsApi } from "../../api/projects";
import { Button } from "../common/Button";
import { ConfirmDialog } from "../common/ConfirmDialog";
import type { Project } from "../../types/models";
import "./ProjectList.css";

interface ProjectListProps {
  onEdit: (project: Project) => void;
  onDeleted: () => void;
}

export function ProjectList({ onEdit, onDeleted }: ProjectListProps) {
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  async function handleDelete() {
    if (!deletingProject) return;

    setDeleteLoading(true);
    try {
      await projectsApi.delete(deletingProject.id);
      setDeletingProject(null);
      onDeleted();
    } catch (err) {
      console.error("Failed to delete project:", err);
    } finally {
      setDeleteLoading(false);
    }
  }

  if (projectsLoading.value) {
    return <div class="project-list__loading">Loading projects...</div>;
  }

  if (projectsError.value) {
    return <div class="project-list__error">{projectsError.value}</div>;
  }

  if (projects.value.length === 0) {
    return (
      <div class="project-list__empty">
        <p>No projects yet. Create your first project to get started.</p>
      </div>
    );
  }

  return (
    <>
      <div class="project-list">
        {projects.value.map((project) => (
          <a
            key={project.id}
            href={`/projects/${project.id}`}
            class="project-card"
          >
            <div class="project-card__content">
              <h3 class="project-card__name">{project.name}</h3>
              {project.description && (
                <p class="project-card__description">{project.description}</p>
              )}
            </div>
            <div class="project-card__actions">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  onEdit(project);
                }}
              >
                Edit
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  setDeletingProject(project);
                }}
              >
                Delete
              </Button>
            </div>
          </a>
        ))}
      </div>

      <ConfirmDialog
        isOpen={!!deletingProject}
        title="Delete Project"
        message={`Are you sure you want to delete "${deletingProject?.name}"? This will also delete all schemes and concepts within it.`}
        confirmLabel={deleteLoading ? "Deleting..." : "Delete"}
        onConfirm={handleDelete}
        onCancel={() => setDeletingProject(null)}
      />
    </>
  );
}
