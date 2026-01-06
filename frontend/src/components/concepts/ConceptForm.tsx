import { useState } from "preact/hooks";
import { Input } from "../common/Input";
import { Button } from "../common/Button";
import { conceptsApi } from "../../api/concepts";
import { ApiError } from "../../api/client";
import type { Concept } from "../../types/models";
import "./ConceptForm.css";

interface ConceptFormProps {
  schemeId: string;
  concept?: Concept | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export function ConceptForm({ schemeId, concept, onSuccess, onCancel }: ConceptFormProps) {
  const [prefLabel, setPrefLabel] = useState(concept?.pref_label ?? "");
  const [definition, setDefinition] = useState(concept?.definition ?? "");
  const [scopeNote, setScopeNote] = useState(concept?.scope_note ?? "");
  const [uri, setUri] = useState(concept?.uri ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const data = {
      pref_label: prefLabel,
      definition: definition || null,
      scope_note: scopeNote || null,
      uri: uri || null,
    };

    try {
      if (concept) {
        await conceptsApi.update(concept.id, data);
      } else {
        await conceptsApi.create(schemeId, data);
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

      <Input
        label="URI"
        name="uri"
        type="url"
        value={uri}
        placeholder="https://example.org/concept"
        onChange={setUri}
      />

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
