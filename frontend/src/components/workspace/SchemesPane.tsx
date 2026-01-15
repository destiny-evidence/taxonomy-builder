import { projects } from "../../state/projects";
import { schemes } from "../../state/schemes";
import "./SchemesPane.css";

interface SchemesPaneProps {
  projectId: string;
  currentSchemeId: string | null;
  onSchemeSelect: (schemeId: string) => void;
  onProjectChange: (projectId: string) => void;
}

export function SchemesPane({
  projectId,
  currentSchemeId,
  onSchemeSelect,
  onProjectChange,
}: SchemesPaneProps) {
  const projectSchemes = schemes.value.filter((s) => s.project_id === projectId);

  return (
    <div class="schemes-pane">
      <div class="schemes-pane__header">
        <select
          class="schemes-pane__project-select"
          value={projectId}
          onChange={(e) => onProjectChange((e.target as HTMLSelectElement).value)}
        >
          {projects.value.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
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
