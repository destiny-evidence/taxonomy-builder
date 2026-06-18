import { useEffect } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { DndContext, type DragEndEvent } from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Button } from "../common/Button";
import { currentProject } from "../../state/projects";
import { schemes, reorderSchemes } from "../../state/schemes";
import { ontologyClasses, selectedClassUri } from "../../state/classes";
import { selectionMode } from "../../state/workspace";
import { feedbackManagerApi } from "../../api/feedback";
import { schemesApi } from "../../api/schemes";
import type { ConceptScheme } from "../../types/models";
import "./ProjectPane.css";

interface SortableSchemeItemProps {
  scheme: ConceptScheme;
  selected: boolean;
  onSelect: (schemeId: string) => void;
}

function SortableSchemeItem({
  scheme,
  selected,
  onSelect,
}: SortableSchemeItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: scheme.id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };
  // Cast attributes to avoid React/Preact type conflicts
  const dndAttributes = attributes as unknown as Record<string, unknown>;

  return (
    <div
      ref={setNodeRef}
      class="project-pane__sortable-item"
      style={style}
      {...dndAttributes}
    >
      <span
        class="project-pane__drag-handle"
        title="Drag to reorder"
        {...listeners}
      >
        ⋮⋮
      </span>
      <button
        class={`project-pane__item ${selected ? "project-pane__item--selected" : ""}`}
        onClick={() => onSelect(scheme.id)}
      >
        {scheme.title}
      </button>
    </div>
  );
}

interface ProjectPaneProps {
  projectId: string;
  currentSchemeId: string | null;
  onSchemeSelect: (schemeId: string) => void;
  onClassSelect: (classUri: string) => void;
  onNewClass: () => void;
  onNewScheme: () => void;
  onImport: () => void;
  onPublish: () => void;
  onVersions: () => void;
  readOnly?: boolean;
}

export function ProjectPane({
  projectId,
  currentSchemeId,
  onSchemeSelect,
  onClassSelect,
  onNewClass,
  onNewScheme,
  onImport,
  onPublish,
  onVersions,
  readOnly = false,
}: ProjectPaneProps) {
  const projectSchemes = schemes.value.filter(
    (s) => s.project_id === projectId,
  );
  const project = currentProject.value;
  const classes = ontologyClasses.value;
  const feedbackCount = useSignal(0);

  useEffect(() => {
    feedbackManagerApi.counts([projectId]).then((counts) => {
      feedbackCount.value = counts[projectId] ?? 0;
    }).catch(() => {});
  }, [projectId]);

  const isClassSelected = (uri: string) =>
    selectionMode.value === "class" && selectedClassUri.value === uri;

  const isSchemeSelected = (id: string) =>
    selectionMode.value === "scheme" && currentSchemeId === id;

  const handleSchemeDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const result = reorderSchemes(
      schemes.value,
      projectId,
      String(active.id),
      String(over.id),
    );
    if (!result) return;

    const previous = schemes.value;
    schemes.value = result.schemes; // optimistic
    try {
      await schemesApi.setPosition(String(active.id), result.newIndex);
    } catch (error) {
      console.error("Failed to reorder scheme:", error);
      schemes.value = previous; // rollback
    }
  };

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
      </div>

      <div class="project-pane__publish-section">
        <span class="project-pane__section-title">Publishing</span>
        <div class="project-pane__publish-group">
          <button class="project-pane__publish-btn" onClick={onPublish}>
            New Version
          </button>
          <button class="project-pane__versions-btn" onClick={onVersions}>
            History
          </button>
        </div>
        <a
          href={`/projects/${projectId}/feedback`}
          class="project-pane__feedback-btn"
        >
          Feedback
          {feedbackCount.value > 0 && (
            <span class="project-pane__feedback-count">
              {feedbackCount.value}
            </span>
          )}
        </a>
      </div>

      <div class="project-pane__content">
        {/* Classes section */}
        <div class="project-pane__section">
          <h3 class="project-pane__section-title">Classes</h3>
          {classes.length === 0 ? (
            <div class="project-pane__empty">No classes in this project</div>
          ) : (
            <div class="project-pane__list">
              {classes.map((cls) => (
                <button
                  key={cls.uri}
                  class={`project-pane__item ${isClassSelected(cls.uri) ? "project-pane__item--selected" : ""}`}
                  onClick={() => onClassSelect(cls.uri)}
                  title={cls.description ?? undefined}
                >
                  {cls.label}
                </button>
              ))}
            </div>
          )}
          <button class="project-pane__add-button" onClick={onNewClass}>
            + New Class
          </button>
        </div>

        {/* Schemes section */}
        <div class="project-pane__section">
          <h3 class="project-pane__section-title">Schemes</h3>
          {projectSchemes.length === 0 ? (
            <div class="project-pane__empty">No schemes in this project</div>
          ) : readOnly ? (
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
          ) : (
            <DndContext onDragEnd={handleSchemeDragEnd}>
              <SortableContext
                items={projectSchemes.map((s) => s.id)}
                strategy={verticalListSortingStrategy}
              >
                <div class="project-pane__list">
                  {projectSchemes.map((scheme) => (
                    <SortableSchemeItem
                      key={scheme.id}
                      scheme={scheme}
                      selected={isSchemeSelected(scheme.id)}
                      onSelect={onSchemeSelect}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          )}
          <button class="project-pane__add-button" onClick={onNewScheme}>
            + New Scheme
          </button>
        </div>
      </div>
    </div>
  );
}
