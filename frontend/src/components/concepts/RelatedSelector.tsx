import { useState } from "preact/hooks";
import { Button } from "../common/Button";
import { conceptsApi } from "../../api/concepts";
import type { Concept, ConceptBrief } from "../../types/models";
import "./RelatedSelector.css";

interface RelatedSelectorProps {
  conceptId: string;
  currentRelated: ConceptBrief[];
  availableConcepts: Concept[];
  onChanged: () => void;
}

export function RelatedSelector({
  conceptId,
  currentRelated,
  availableConcepts,
  onChanged,
}: RelatedSelectorProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(false);

  // Filter out concepts that are already related
  const relatedIds = new Set(currentRelated.map((r) => r.id));
  const addableConcepts = availableConcepts.filter((c) => !relatedIds.has(c.id));

  async function handleAdd() {
    if (!selectedId) return;

    setLoading(true);
    try {
      await conceptsApi.addRelated(conceptId, selectedId);
      setSelectedId("");
      setIsAdding(false);
      onChanged();
    } catch (err) {
      console.error("Failed to add related:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRemove(relatedId: string) {
    setLoading(true);
    try {
      await conceptsApi.removeRelated(conceptId, relatedId);
      onChanged();
    } catch (err) {
      console.error("Failed to remove related:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div class="related-selector">
      {currentRelated.length > 0 ? (
        <ul class="related-selector__list">
          {currentRelated.map((related) => (
            <li key={related.id} class="related-selector__item">
              <span class="related-selector__label">{related.pref_label}</span>
              <button
                class="related-selector__remove"
                onClick={() => handleRemove(related.id)}
                disabled={loading}
                title="Remove related relationship"
              >
                &times;
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p class="related-selector__empty">No related concepts</p>
      )}

      {isAdding ? (
        <div class="related-selector__add-form">
          <select
            class="related-selector__select"
            value={selectedId}
            onChange={(e) => setSelectedId(e.currentTarget.value)}
            disabled={loading}
          >
            <option value="">Select a concept...</option>
            {addableConcepts.map((concept) => (
              <option key={concept.id} value={concept.id}>
                {concept.pref_label}
              </option>
            ))}
          </select>
          <Button size="sm" onClick={handleAdd} disabled={!selectedId || loading}>
            Add
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setIsAdding(false)}>
            Cancel
          </Button>
        </div>
      ) : (
        addableConcepts.length > 0 && (
          <Button variant="ghost" size="sm" onClick={() => setIsAdding(true)}>
            + Add Related
          </Button>
        )
      )}
    </div>
  );
}
