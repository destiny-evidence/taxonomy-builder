import { Button } from "../common/Button";
import { currentProject } from "../../state/projects";
import { schemes } from "../../state/schemes";
import "./SchemesPane.css";

interface SchemesPaneProps {
  projectId: string;
  currentSchemeId: string | null;
  onSchemeSelect: (schemeId: string) => void;
  onNewScheme: () => void;
  onImport: () => void;
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

        {selectedScheme && (
          <div class="schemes-pane__detail">
            <div class="schemes-pane__detail-header">
              <h3 class="schemes-pane__detail-title" data-testid="scheme-detail-title">
                {selectedScheme.title}
              </h3>
            </div>

            <div class="schemes-pane__detail-content">
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
