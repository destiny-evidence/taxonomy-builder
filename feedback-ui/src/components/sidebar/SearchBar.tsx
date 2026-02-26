import { signal } from "@preact/signals";
import { navigate } from "../../router";
import { selectedVersion, currentProjectId } from "../../state/vocabulary";
import { searchQuery, searchResults, type SearchResult } from "../../state/search";
import type { EntityKind } from "../../router";
import "./SearchBar.css";

const GROUP_ORDER: SearchResult["type"][] = [
  "concept",
  "scheme",
  "class",
  "property",
  "feedback",
];

const GROUP_LABELS: Record<SearchResult["type"], string> = {
  concept: "Concepts",
  scheme: "Schemes",
  class: "Classes",
  property: "Properties",
  feedback: "Feedback",
};

/** Keyboard-driven highlight index (-1 = none). */
const activeIndex = signal(-1);

export function SearchBar() {
  const results = searchResults.value;
  const hasQuery = searchQuery.value.trim().length > 0;
  const highlighted = activeIndex.value;

  // Flatten results in display order for keyboard navigation
  const flatResults: SearchResult[] = [];
  const grouped = new Map<SearchResult["type"], SearchResult[]>();
  for (const r of results) {
    const list = grouped.get(r.type);
    if (list) list.push(r);
    else grouped.set(r.type, [r]);
  }
  for (const type of GROUP_ORDER) {
    const group = grouped.get(type);
    if (group) flatResults.push(...group);
  }

  function selectResult(result: SearchResult) {
    const version = selectedVersion.value;
    const projectId = currentProjectId.value;
    if (!version || !projectId) return;

    if (result.type === "feedback" && result.entityType && result.entityId) {
      navigate(projectId, version, result.entityType as EntityKind, result.entityId);
    } else if (result.type !== "feedback") {
      navigate(projectId, version, result.type, result.id);
    }
    searchQuery.value = "";
    activeIndex.value = -1;
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (!hasQuery || flatResults.length === 0) {
      if (e.key === "Escape") { searchQuery.value = ""; activeIndex.value = -1; }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        activeIndex.value = Math.min(highlighted + 1, flatResults.length - 1);
        break;
      case "ArrowUp":
        e.preventDefault();
        activeIndex.value = Math.max(highlighted - 1, 0);
        break;
      case "Enter":
        if (highlighted >= 0 && highlighted < flatResults.length) {
          e.preventDefault();
          selectResult(flatResults[highlighted]);
        }
        break;
      case "Escape":
        searchQuery.value = "";
        activeIndex.value = -1;
        break;
    }
  }

  // Track position of each result in flat list
  let flatIndex = 0;

  return (
    <div class="search-bar">
      <input
        class="search-bar__input"
        type="search"
        aria-label="Search vocabulary"
        placeholder="Search..."
        value={searchQuery.value}
        onInput={(e) => {
          searchQuery.value = (e.target as HTMLInputElement).value;
          activeIndex.value = -1;
        }}
        onKeyDown={handleKeyDown}
      />
      {hasQuery && (
        <div class="search-results" role="listbox">
          {flatResults.length === 0 ? (
            <div class="search-results__empty">No results</div>
          ) : (
            GROUP_ORDER.filter((type) => grouped.has(type)).map((type) => (
              <div key={type}>
                <div class="search-results__group-title">
                  {GROUP_LABELS[type]}
                </div>
                {grouped.get(type)!.map((r) => {
                  const idx = flatIndex++;
                  const isActive = idx === highlighted;
                  return (
                    <div
                      key={`${r.type}-${r.id}`}
                      class={`search-results__item${isActive ? " search-results__item--active" : ""}`}
                      role="option"
                      aria-selected={isActive}
                      onClick={() => selectResult(r)}
                    >
                      <div>{r.label}</div>
                      {r.snippet && (
                        <div class="search-results__snippet">{r.snippet}</div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
