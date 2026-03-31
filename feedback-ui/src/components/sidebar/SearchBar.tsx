import { searchQuery, expandMatchingPaths, clearSearch } from "../../state/search";
import "./SearchBar.css";

let debounceTimer: number;

export function SearchBar() {
  const query = searchQuery.value;
  const hasQuery = query.trim().length > 0;

  function handleInput(e: Event) {
    const value = (e.target as HTMLInputElement).value;
    searchQuery.value = value;
    clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(() => {
      expandMatchingPaths(value);
    }, 200);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      clearTimeout(debounceTimer);
      clearSearch();
    }
  }

  function handleClear() {
    clearTimeout(debounceTimer);
    clearSearch();
  }

  return (
    <div class="search-bar">
      <div class="search-bar__wrapper">
        <input
          class="search-bar__input"
          type="search"
          aria-label="Search vocabulary"
          placeholder="Search..."
          value={query}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
        />
        {hasQuery && (
          <button
            type="button"
            class="search-bar__clear"
            aria-label="Clear search"
            onClick={handleClear}
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
