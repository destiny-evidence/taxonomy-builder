import { useState, useEffect } from "preact/hooks";
import { Input } from "../common/Input";
import { Button } from "../common/Button";
import { AltLabelsEditor } from "./AltLabelsEditor";
import { conceptsApi } from "../../api/concepts";
import { ApiError } from "../../api/client";
import type { Concept } from "../../types/models";
import "./ConceptForm.css";

interface ConceptFormProps {
  schemeId: string;
  concept?: Concept | null;
  initialBroaderId?: string | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export function ConceptForm({ schemeId, concept, initialBroaderId, onSuccess, onCancel }: ConceptFormProps) {
  const [prefLabel, setPrefLabel] = useState(concept?.pref_label ?? "");
  const [definition, setDefinition] = useState(concept?.definition ?? "");
  const [scopeNote, setScopeNote] = useState(concept?.scope_note ?? "");
  const [altLabels, setAltLabels] = useState<string[]>(concept?.alt_labels ?? []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync form state when concept prop changes (for edit vs create)
  useEffect(() => {
    setPrefLabel(concept?.pref_label ?? "");
    setDefinition(concept?.definition ?? "");
    setScopeNote(concept?.scope_note ?? "");
    setAltLabels(concept?.alt_labels ?? []);
    setError(null);
  }, [concept]);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const data = {
      pref_label: prefLabel,
      definition: definition || null,
      scope_note: scopeNote || null,
      alt_labels: altLabels,
    };

    try {
      if (concept) {
        await conceptsApi.update(concept.id, data);
      } else {
        const newConcept = await conceptsApi.create(schemeId, data);
        // Add broader relationship if initialBroaderId was provided
        if (initialBroaderId) {
          await conceptsApi.addBroader(newConcept.id, initialBroaderId);
        }
      }
      onSuccess();
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
    <form class="concept-form" onSubmit={handleSubmit}>
      {error && <div class="concept-form__error">{error}</div>}

      <Input
        label="Preferred Label"
        name="pref_label"
        value={prefLabel}
        placeholder="Enter the concept name"
        required
        onChange={setPrefLabel}
      />

      <Input
        label="Definition"
        name="definition"
        value={definition}
        placeholder="A formal definition of the concept"
        multiline
        onChange={setDefinition}
      />

      <Input
        label="Scope Note"
        name="scope_note"
        value={scopeNote}
        placeholder="Usage guidance and scope clarification"
        multiline
        onChange={setScopeNote}
      />

      <div class="concept-form__field">
        <label class="concept-form__field-label">Alternative Labels</label>
        <AltLabelsEditor labels={altLabels} onChange={setAltLabels} />
      </div>

      <div class="concept-form__actions">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading || !prefLabel.trim()}>
          {loading ? "Saving..." : concept ? "Save Changes" : "Create Concept"}
        </Button>
      </div>
    </form>
  );
}
