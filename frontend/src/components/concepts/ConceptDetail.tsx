import { useState } from "preact/hooks";
import { Button } from "../common/Button";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { AltLabelsEditor } from "./AltLabelsEditor";
import { BroaderSelector } from "./BroaderSelector";
import { RelatedSelector } from "./RelatedSelector";
import { concepts } from "../../state/concepts";
import type { Concept } from "../../types/models";
import "./ConceptDetail.css";

interface ConceptDetailProps {
  concept: Concept;
  onEdit: () => void;
  onDelete: () => void;
  onRefresh: () => void;
}

export function ConceptDetail({ concept, onEdit, onDelete, onRefresh }: ConceptDetailProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Get available concepts for broader selector (exclude self)
  const availableConcepts = concepts.value.filter((c) => c.id !== concept.id);

  return (
    <div class="concept-detail">
      <div class="concept-detail__header">
        <h2 class="concept-detail__title">{concept.pref_label}</h2>
        <div class="concept-detail__actions">
          <Button variant="ghost" size="sm" onClick={onEdit}>
            Edit
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setShowDeleteConfirm(true)}>
            Delete
          </Button>
        </div>
      </div>

      <div class="concept-detail__content">
        {concept.definition && (
          <div class="concept-detail__field">
            <label class="concept-detail__label">Definition</label>
            <p class="concept-detail__value">{concept.definition}</p>
          </div>
        )}

        {concept.scope_note && (
          <div class="concept-detail__field">
            <label class="concept-detail__label">Scope Note</label>
            <p class="concept-detail__value">{concept.scope_note}</p>
          </div>
        )}

        {concept.uri && (
          <div class="concept-detail__field">
            <label class="concept-detail__label">URI</label>
            <p class="concept-detail__value">
              <a href={concept.uri} target="_blank" rel="noopener noreferrer">
                {concept.uri}
              </a>
            </p>
          </div>
        )}

        <div class="concept-detail__field">
          <label class="concept-detail__label">Alternative Labels</label>
          <AltLabelsEditor
            labels={concept.alt_labels}
            onChange={() => {}}
            readOnly
          />
        </div>

        <div class="concept-detail__field">
          <label class="concept-detail__label">Broader Concepts</label>
          <BroaderSelector
            conceptId={concept.id}
            currentBroader={concept.broader}
            availableConcepts={availableConcepts}
            onChanged={onRefresh}
          />
        </div>

        <div class="concept-detail__field">
          <label class="concept-detail__label">Related Concepts</label>
          <RelatedSelector
            conceptId={concept.id}
            currentRelated={concept.related}
            availableConcepts={availableConcepts}
            onChanged={onRefresh}
          />
        </div>

        <div class="concept-detail__meta">
          <span>Created: {new Date(concept.created_at).toLocaleDateString()}</span>
          <span>Updated: {new Date(concept.updated_at).toLocaleDateString()}</span>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete Concept"
        message={`Are you sure you want to delete "${concept.pref_label}"? This action cannot be undone.`}
        confirmLabel="Delete"
        onConfirm={() => {
          setShowDeleteConfirm(false);
          onDelete();
        }}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
