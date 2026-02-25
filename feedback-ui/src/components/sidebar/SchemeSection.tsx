import { useSignal } from "@preact/signals";
import { navigate, route } from "../../router";
import { selectedVersion, currentProjectId, conceptTrees } from "../../state/vocabulary";
import { isAuthenticated } from "../../state/auth";
import { feedbackCountForEntity } from "../../state/feedback";
import { ConceptTree } from "./ConceptTree";
import type { VocabScheme } from "../../api/published";

interface SchemeSectionProps {
  scheme: VocabScheme;
}

export function SchemeSection({ scheme }: SchemeSectionProps) {
  const expanded = useSignal(false);
  const isActive =
    route.value.entityKind === "scheme" && route.value.entityId === scheme.id;

  function handleTitleClick() {
    const version = selectedVersion.value;
    const projectId = currentProjectId.value;
    if (version && projectId) {
      navigate(projectId, version, "scheme", scheme.id);
    }
  }

  const tree = conceptTrees.value.get(scheme.id) ?? [];

  const displayCount = (() => {
    if (!isAuthenticated.value) return 0;
    const ownCount = feedbackCountForEntity(scheme.id, "scheme");
    if (expanded.value) return ownCount;
    const conceptCount = Object.keys(scheme.concepts).reduce(
      (sum, id) => sum + feedbackCountForEntity(id, "concept"), 0
    );
    return ownCount + conceptCount;
  })();

  return (
    <div class="sidebar__section">
      <div class="sidebar__section-header" onClick={() => (expanded.value = !expanded.value)}>
        <svg class={`sidebar__chevron${expanded.value ? " sidebar__chevron--open" : ""}`} width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span
          class={`sidebar__section-title${isActive ? " sidebar__section-title--active" : ""}`}
          onClick={(e: Event) => {
            e.stopPropagation();
            handleTitleClick();
          }}
        >
          {scheme.title}
        </span>
        {displayCount > 0 && <span class="sidebar__badge">{displayCount}</span>}
      </div>
      {expanded.value && <ConceptTree nodes={tree} schemeId={scheme.id} />}
    </div>
  );
}
