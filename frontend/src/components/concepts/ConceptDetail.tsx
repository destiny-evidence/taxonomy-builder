import { useState, useEffect } from "preact/hooks";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { AltLabelsEditor } from "./AltLabelsEditor";
import { BroaderSelector } from "./BroaderSelector";
import { RelatedSelector } from "./RelatedSelector";
import { conceptsApi } from "../../api/concepts";
import { ApiError } from "../../api/client";
import { concepts } from "../../state/concepts";
import type { Concept } from "../../types/models";
import "./ConceptDetail.css";

interface ConceptDetailProps {
  concept: Concept;
  onDelete: () => void;
  onRefresh: () => void;
}

export function ConceptDetail({ concept, onDelete, onRefresh }: ConceptDetailProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [prefLabel, setPrefLabel] = useState(concept.pref_label);
  const [identifier, setIdentifier] = useState(concept.identifier ?? "");
  const [definition, setDefinition] = useState(concept.definition ?? "");
  const [scopeNote, setScopeNote] = useState(concept.scope_note ?? "");
  const [altLabels, setAltLabels] = useState<string[]>(concept.alt_labels);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync state when concept changes
  useEffect(() => {
    setPrefLabel(concept.pref_label);
    setIdentifier(concept.identifier ?? "");
    setDefinition(concept.definition ?? "");
    setScopeNote(concept.scope_note ?? "");
    setAltLabels(concept.alt_labels);
    setIsEditing(false); // Exit edit mode when concept changes
    setError(null);
  }, [concept.id]);

  // Get available concepts for broader selector (exclude self)
  const availableConcepts = concepts.value.filter((c) => c.id !== concept.id);

  function handleEditClick() {
    setIsEditing(true);
  }

  function handleCancel() {
    // Reset all fields to original concept values
    setPrefLabel(concept.pref_label);
    setIdentifier(concept.identifier ?? "");
    setDefinition(concept.definition ?? "");
    setScopeNote(concept.scope_note ?? "");
    setAltLabels(concept.alt_labels);
    setError(null);
    setIsEditing(false);
  }

  async function handleSave() {
    setLoading(true);
    setError(null);

    const data = {
      pref_label: prefLabel,
      identifier: identifier || null,
      definition: definition || null,
      scope_note: scopeNote || null,
      alt_labels: altLabels,
    };

    try {
      await conceptsApi.update(concept.id, data);
      onRefresh();
      setIsEditing(false);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "An error occurred");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div class={`concept-detail ${isEditing ? 'concept-detail--editing' : ''}`}>
      <div class="concept-detail__header">
        {!isEditing ? (
          <h2 class="concept-detail__title">{concept.pref_label}</h2>
        ) : (
          <div class="concept-detail__field">
            <Input
              label="Preferred Label"
              name="pref_label"
              value={prefLabel}
              required
              onChange={setPrefLabel}
            />
          </div>
        )}
        <div class="concept-detail__actions">
          {!isEditing ? (
            <>
              <Button variant="ghost" size="sm" onClick={handleEditClick}>
                Edit
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowDeleteConfirm(true)}>
                Delete
              </Button>
            </>
          ) : (
            <>
              <Button variant="secondary" size="sm" onClick={handleCancel} disabled={loading}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleSave} disabled={loading || !prefLabel.trim()}>
                {loading ? "Saving..." : "Save Changes"}
              </Button>
            </>
          )}
        </div>
      </div>

      {error && isEditing && (
        <div class="concept-detail__error">{error}</div>
      )}

      <div class="concept-detail__content">
        {isEditing ? (
          <>
            <div class="concept-detail__field">
              <Input
                label="Identifier"
                name="identifier"
                value={identifier}
                placeholder="e.g., 001 or my-concept"
                onChange={setIdentifier}
              />
            </div>

            <div class="concept-detail__field">
              <Input
                label="Definition"
                name="definition"
                value={definition}
                placeholder="A formal definition of the concept"
                multiline
                onChange={setDefinition}
              />
            </div>

            <div class="concept-detail__field">
              <Input
                label="Scope Note"
                name="scope_note"
                value={scopeNote}
                placeholder="Usage guidance and scope clarification"
                multiline
                onChange={setScopeNote}
              />
            </div>

            <div class="concept-detail__field">
              <label class="concept-detail__label">Alternative Labels</label>
              <AltLabelsEditor labels={altLabels} onChange={setAltLabels} />
            </div>
          </>
        ) : (
          <>
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
          </>
        )}

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
