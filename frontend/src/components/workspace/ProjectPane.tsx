import { Button } from "../common/Button";
import { currentProject } from "../../state/projects";
import { schemes } from "../../state/schemes";
import { ontologyClasses, selectedClassUri } from "../../state/ontology";
import { selectionMode } from "../../state/workspace";
import "./ProjectPane.css";

interface ProjectPaneProps {
  projectId: string;
  currentSchemeId: string | null;
  onSchemeSelect: (schemeId: string) => void;
  onClassSelect: (classUri: string) => void;
  onNewScheme: () => void;
  onImport: () => void;
  onPublish: () => void;
  onVersions: () => void;
  draft?: { version: string; title: string } | null;
}

export function ProjectPane({
  projectId,
  currentSchemeId,
  onSchemeSelect,
  onClassSelect,
  onNewScheme,
  onImport,
  onPublish,
  onVersions,
  draft = null,
}: ProjectPaneProps) {
  const projectSchemes = schemes.value.filter((s) => s.project_id === projectId);
  const project = currentProject.value;
  const classes = ontologyClasses.value;

  const isClassSelected = (uri: string) =>
    selectionMode.value === "class" && selectedClassUri.value === uri;

  const isSchemeSelected = (id: string) =>
    selectionMode.value === "scheme" && currentSchemeId === id;

  return (
    <div class="project-pane">
      <div class="project-pane__header">
        <a href="/projects" class="project-pane__back-link">
          Projects
        </a>
        <div class="project-pane__header-row">
          <h2 class="project-pane__project-title">{project?.name}</h2>
          <Button variant="ghost" size="sm" onClick={onImport}>
            Import
          </Button>
        </div>
        <div class={`project-pane__publish-group ${draft ? "project-pane__publish-group--draft" : ""}`}>
          <button
            class="project-pane__publish-btn"
            onClick={onPublish}
          >
            {draft ? `Drafting v${draft.version}\u2026` : "Publish"}
          </button>
          <button
            class="project-pane__versions-btn"
            onClick={onVersions}
            aria-label="Version history"
          >
            {"\u2261"}
          </button>
        </div>
      </div>

      <div class="project-pane__content">
        {/* Classes section */}
        <div class="project-pane__section">
          <h3 class="project-pane__section-title">Classes</h3>
          <div class="project-pane__list">
            {classes.map((cls) => (
              <button
                key={cls.uri}
                class={`project-pane__item ${isClassSelected(cls.uri) ? "project-pane__item--selected" : ""}`}
                onClick={() => onClassSelect(cls.uri)}
                title={cls.comment ?? undefined}
              >
                {cls.label}
              </button>
            ))}
          </div>
        </div>

        {/* Schemes section */}
        <div class="project-pane__section">
          <h3 class="project-pane__section-title">Schemes</h3>
          {projectSchemes.length === 0 ? (
            <div class="project-pane__empty">No schemes in this project</div>
          ) : (
            <div class="project-pane__list">
              {projectSchemes.map((scheme) => (
                <button
                  key={scheme.id}
                  class={`project-pane__item ${isSchemeSelected(scheme.id) ? "project-pane__item--selected" : ""}`}
                  onClick={() => onSchemeSelect(scheme.id)}
                >
                  {scheme.title}
                </button>
              ))}
            </div>
          )}
          <button class="project-pane__add-button" onClick={onNewScheme}>
            + New Scheme
          </button>
        </div>
      </div>
    </div>
  );
}
