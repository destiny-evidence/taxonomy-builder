import { vocabulary, loading, error } from "../../state/vocabulary";
import { searchQuery } from "../../state/search";
import { VersionSelector } from "./VersionSelector";
import { SearchBar } from "./SearchBar";
import { SchemeSection } from "./SchemeSection";
import { DataModelSection } from "./DataModelSection";
import "./Sidebar.css";

export function Sidebar() {
  if (loading.value) {
    return <div class="sidebar"><p class="sidebar__empty">Loading...</p></div>;
  }

  if (error.value) {
    return (
      <div class="sidebar">
        <p class="sidebar__empty" style="color: var(--color-danger)">
          {error.value}
        </p>
      </div>
    );
  }

  const vocab = vocabulary.value;
  if (!vocab) {
    return <div class="sidebar"><p class="sidebar__empty">No content published yet</p></div>;
  }

  const hasSearchQuery = searchQuery.value.trim().length > 0;

  return (
    <div class="sidebar">
      <VersionSelector />
      <SearchBar />
      {!hasSearchQuery && (
        <>
          {vocab.schemes.map((scheme) => (
            <SchemeSection key={scheme.id} scheme={scheme} />
          ))}
          <DataModelSection />
        </>
      )}
    </div>
  );
}
