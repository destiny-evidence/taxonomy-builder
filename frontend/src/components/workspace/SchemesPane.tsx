import { Button } from "../common/Button";
import { currentProject } from "../../state/projects";
import { schemes } from "../../state/schemes";
import "./SchemesPane.css";

interface SchemesPaneProps {
  projectId: string;
  currentSchemeId: string | null;
  showProperties: boolean;
  onSchemeSelect: (schemeId: string) => void;
  onPropertiesSelect: () => void;
  onNewScheme: () => void;
  onImport: () => void;
}

export function SchemesPane({
  projectId,
  currentSchemeId,
  showProperties,
  onSchemeSelect,
  onPropertiesSelect,
  onNewScheme,
  onImport,
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
        <div class="schemes-pane__nav">
          <button
            class={`schemes-pane__item ${showProperties ? "schemes-pane__item--selected" : ""}`}
            onClick={onPropertiesSelect}
          >
            Properties
          </button>
        </div>

        <div class="schemes-pane__section-label">Schemes</div>

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
