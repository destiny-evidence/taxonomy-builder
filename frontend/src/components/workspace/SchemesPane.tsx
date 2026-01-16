import { currentProject } from "../../state/projects";
import { schemes } from "../../state/schemes";
import "./SchemesPane.css";

interface SchemesPaneProps {
  projectId: string;
  currentSchemeId: string | null;
  onSchemeSelect: (schemeId: string) => void;
}

export function SchemesPane({
  projectId,
  currentSchemeId,
  onSchemeSelect,
}: SchemesPaneProps) {
  const projectSchemes = schemes.value.filter((s) => s.project_id === projectId);
  const project = currentProject.value;

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
      </div>
    </div>
  );
}
