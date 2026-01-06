import { useState } from "preact/hooks";
import { Button } from "../common/Button";
import { conceptsApi } from "../../api/concepts";
import type { Concept, ConceptBrief } from "../../types/models";
import "./BroaderSelector.css";

interface BroaderSelectorProps {
  conceptId: string;
  currentBroader: ConceptBrief[];
  availableConcepts: Concept[];
  onChanged: () => void;
}

export function BroaderSelector({
  conceptId,
  currentBroader,
  availableConcepts,
  onChanged,
}: BroaderSelectorProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(false);

  // Filter out concepts that are already broader
  const broaderIds = new Set(currentBroader.map((b) => b.id));
  const addableConcepts = availableConcepts.filter((c) => !broaderIds.has(c.id));

  async function handleAdd() {
    if (!selectedId) return;

    setLoading(true);
    try {
      await conceptsApi.addBroader(conceptId, selectedId);
      setSelectedId("");
      setIsAdding(false);
      onChanged();
    } catch (err) {
      console.error("Failed to add broader:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRemove(broaderId: string) {
    setLoading(true);
    try {
      await conceptsApi.removeBroader(conceptId, broaderId);
      onChanged();
    } catch (err) {
      console.error("Failed to remove broader:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div class="broader-selector">
      {currentBroader.length > 0 ? (
        <ul class="broader-selector__list">
          {currentBroader.map((broader) => (
            <li key={broader.id} class="broader-selector__item">
              <span class="broader-selector__label">{broader.pref_label}</span>
              <button
                class="broader-selector__remove"
                onClick={() => handleRemove(broader.id)}
                disabled={loading}
                title="Remove broader relationship"
              >
                &times;
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p class="broader-selector__empty">No broader concepts (this is a root concept)</p>
      )}

      {isAdding ? (
        <div class="broader-selector__add-form">
          <select
            class="broader-selector__select"
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
            + Add Broader
          </Button>
        )
      )}
    </div>
  );
}
