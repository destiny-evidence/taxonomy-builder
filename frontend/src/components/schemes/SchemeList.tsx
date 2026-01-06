import { useState } from "preact/hooks";
import { schemes, schemesLoading, schemesError } from "../../state/schemes";
import { schemesApi } from "../../api/schemes";
import { Button } from "../common/Button";
import { ConfirmDialog } from "../common/ConfirmDialog";
import type { ConceptScheme } from "../../types/models";
import "./SchemeList.css";

interface SchemeListProps {
  onEdit: (scheme: ConceptScheme) => void;
  onDeleted: () => void;
}

export function SchemeList({ onEdit, onDeleted }: SchemeListProps) {
  const [deletingScheme, setDeletingScheme] = useState<ConceptScheme | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  async function handleDelete() {
    if (!deletingScheme) return;

    setDeleteLoading(true);
    try {
      await schemesApi.delete(deletingScheme.id);
      setDeletingScheme(null);
      onDeleted();
    } catch (err) {
      console.error("Failed to delete scheme:", err);
    } finally {
      setDeleteLoading(false);
    }
  }

  if (schemesLoading.value) {
    return <div class="scheme-list__loading">Loading schemes...</div>;
  }

  if (schemesError.value) {
    return <div class="scheme-list__error">{schemesError.value}</div>;
  }

  if (schemes.value.length === 0) {
    return (
      <div class="scheme-list__empty">
        <p>No concept schemes yet. Create your first scheme to start building your taxonomy.</p>
      </div>
    );
  }

  return (
    <>
      <div class="scheme-list">
        {schemes.value.map((scheme) => (
          <a
            key={scheme.id}
            href={`/schemes/${scheme.id}`}
            class="scheme-card"
          >
            <div class="scheme-card__content">
              <h3 class="scheme-card__title">{scheme.title}</h3>
              {scheme.description && (
                <p class="scheme-card__description">{scheme.description}</p>
              )}
              <div class="scheme-card__meta">
                {scheme.version && (
                  <span class="scheme-card__version">v{scheme.version}</span>
                )}
                {scheme.publisher && (
                  <span class="scheme-card__publisher">{scheme.publisher}</span>
                )}
              </div>
            </div>
            <div
              class="scheme-card__actions"
              onClick={(e) => e.preventDefault()}
            >
              <Button variant="ghost" size="sm" onClick={() => onEdit(scheme)}>
                Edit
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDeletingScheme(scheme)}
              >
                Delete
              </Button>
            </div>
          </a>
        ))}
      </div>

      <ConfirmDialog
        isOpen={!!deletingScheme}
        title="Delete Concept Scheme"
        message={`Are you sure you want to delete "${deletingScheme?.title}"? This will also delete all concepts within it.`}
        confirmLabel={deleteLoading ? "Deleting..." : "Delete"}
        onConfirm={handleDelete}
        onCancel={() => setDeletingScheme(null)}
      />
    </>
  );
}
