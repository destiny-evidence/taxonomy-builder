import { projects, loading, error } from "../../state/vocabulary";
import { navigateToProject, navigateToProjectLatest } from "../../router";
import { LoadingSpinner } from "../common/LoadingOverlay";
import "./ProjectListPage.css";

export function ProjectListPage() {
  if (loading.value) {
    return <div class="project-list"><LoadingSpinner /></div>;
  }

  if (error.value) {
    return (
      <div class="project-list">
        <p class="project-list__status project-list__status--error">{error.value}</p>
      </div>
    );
  }

  if (projects.value.length === 0) {
    return (
      <div class="project-list">
        <p class="project-list__status">No published projects available.</p>
      </div>
    );
  }

  return (
    <div class="project-list">
      <h1 class="project-list__title">Published Vocabularies</h1>
      <div class="project-list__grid">
        {projects.value.map((project) => (
          <button
            key={project.id}
            class="project-card"
            onClick={() =>
              project.latest_version
                ? navigateToProject(project.id, project.latest_version)
                : navigateToProjectLatest(project.id)
            }
          >
            <h2 class="project-card__name">{project.name}</h2>
            {project.description && (
              <p class="project-card__description">{project.description}</p>
            )}
            <span class="project-card__version">
              {project.latest_version ? `v${project.latest_version}` : "No released version"}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
