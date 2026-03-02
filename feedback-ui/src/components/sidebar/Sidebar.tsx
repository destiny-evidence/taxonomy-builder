import { vocabulary, loading, error } from "../../state/vocabulary";
import { searchQuery } from "../../state/search";
import { SearchBar } from "./SearchBar";
import { SchemeSection } from "./SchemeSection";
import { DataModelSection } from "./DataModelSection";
import { LoadingSpinner } from "../common/LoadingOverlay";
import "./Sidebar.css";

export function Sidebar() {
  if (loading.value) {
    return <div class="sidebar"><LoadingSpinner /></div>;
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

  const hasSchemes = vocab.schemes.length > 0;

  return (
    <nav class="sidebar" aria-label="Vocabulary navigation">
      <SearchBar />
      {!hasSearchQuery && (
        <>
          {hasSchemes && (
            <div class="sidebar__group">
              <div class="sidebar__group-header">Concept Schemes</div>
              <div class="sidebar__group-body">
                {vocab.schemes.map((scheme) => (
                  <SchemeSection key={scheme.id} scheme={scheme} />
                ))}
              </div>
            </div>
          )}
          <DataModelSection />
        </>
      )}
    </nav>
  );
}
