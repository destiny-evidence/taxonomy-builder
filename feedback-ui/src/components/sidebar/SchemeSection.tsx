import { useSignal } from "@preact/signals";
import { navigate, route } from "../../router";
import { selectedVersion, conceptTrees } from "../../state/vocabulary";
import { ConceptTree } from "./ConceptTree";
import type { VocabScheme } from "../../api/published";

interface SchemeSectionProps {
  scheme: VocabScheme;
}

export function SchemeSection({ scheme }: SchemeSectionProps) {
  const expanded = useSignal(true);
  const isActive =
    route.value.entityKind === "scheme" && route.value.entityId === scheme.id;

  function handleTitleClick() {
    const version = selectedVersion.value;
    if (version) {
      navigate(version, "scheme", scheme.id);
    }
  }

  const tree = conceptTrees.value.get(scheme.id) ?? [];

  return (
    <div class="sidebar__section">
      <div class="sidebar__section-header" onClick={() => (expanded.value = !expanded.value)}>
        <span
          class={`sidebar__section-title${isActive ? " data-model-item--active" : ""}`}
          onClick={(e: Event) => {
            e.stopPropagation();
            handleTitleClick();
          }}
          style="cursor: pointer"
        >
          {scheme.title}
        </span>
        <span class={`sidebar__toggle${expanded.value ? " sidebar__toggle--open" : ""}`}>
          ▸
        </span>
      </div>
      {expanded.value && <ConceptTree nodes={tree} schemeId={scheme.id} />}
    </div>
  );
}
