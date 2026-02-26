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

export function SearchBar() {
  const results = searchResults.value;
  const hasQuery = searchQuery.value.trim().length > 0;

  function handleClick(result: SearchResult) {
    const version = selectedVersion.value;
    const projectId = currentProjectId.value;
    if (!version || !projectId) return;

    if (result.type === "feedback" && result.entityType && result.entityId) {
      navigate(projectId, version, result.entityType as EntityKind, result.entityId);
    } else if (result.type !== "feedback") {
      navigate(projectId, version, result.type, result.id);
    }
    searchQuery.value = "";
  }

  // Group results by type
  const grouped = new Map<SearchResult["type"], SearchResult[]>();
  for (const r of results) {
    const list = grouped.get(r.type);
    if (list) {
      list.push(r);
    } else {
      grouped.set(r.type, [r]);
    }
  }

  return (
    <div class="search-bar">
      <input
        class="search-bar__input"
        type="search"
        aria-label="Search vocabulary"
        placeholder="Search..."
        value={searchQuery.value}
        onInput={(e) =>
          (searchQuery.value = (e.target as HTMLInputElement).value)
        }
      />
      {hasQuery && (
        <div class="search-results">
          {results.length === 0 ? (
            <div class="search-results__empty">No results</div>
          ) : (
            GROUP_ORDER.filter((type) => grouped.has(type)).map((type) => (
              <div key={type}>
                <div class="search-results__group-title">
                  {GROUP_LABELS[type]}
                </div>
                {grouped.get(type)!.map((r) => (
                  <div
                    key={`${r.type}-${r.id}`}
                    class="search-results__item"
                    onClick={() => handleClick(r)}
                  >
                    <div>{r.label}</div>
                    {r.snippet && (
                      <div class="search-results__snippet">{r.snippet}</div>
                    )}
                  </div>
                ))}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
