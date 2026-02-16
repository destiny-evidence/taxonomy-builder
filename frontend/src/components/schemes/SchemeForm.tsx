import { useState, useEffect } from "preact/hooks";
import { Input } from "../common/Input";
import { Button } from "../common/Button";
import { schemesApi } from "../../api/schemes";
import { ApiError } from "../../api/client";
import type { ConceptScheme } from "../../types/models";
import "./SchemeForm.css";

interface SchemeFormProps {
  projectId: string;
  scheme?: ConceptScheme | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export function SchemeForm({ projectId, scheme, onSuccess, onCancel }: SchemeFormProps) {
  const [title, setTitle] = useState(scheme?.title ?? "");
  const [description, setDescription] = useState(scheme?.description ?? "");
  const [uri, setUri] = useState(scheme?.uri ?? "");
  const [publisher, setPublisher] = useState(scheme?.publisher ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync form state when scheme prop changes (for edit vs create)
  useEffect(() => {
    setTitle(scheme?.title ?? "");
    setDescription(scheme?.description ?? "");
    setUri(scheme?.uri ?? "");
    setPublisher(scheme?.publisher ?? "");
    setError(null);
  }, [scheme]);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const data = {
      title,
      description: description || null,
      uri: uri || null,
      publisher: publisher || null,
    };

    try {
      if (scheme) {
        await schemesApi.update(scheme.id, data);
      } else {
        await schemesApi.create(projectId, data);
      }
      onSuccess();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("A scheme with this title already exists in this project.");
      } else {
        setError(err instanceof Error ? err.message : "An error occurred");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form class="scheme-form" onSubmit={handleSubmit}>
      {error && <div class="scheme-form__error">{error}</div>}

      <Input
        label="Title"
        name="title"
        value={title}
        placeholder="Enter scheme title"
        required
        onChange={setTitle}
      />

      <Input
        label="Description"
        name="description"
        value={description}
        placeholder="Optional description"
        multiline
        onChange={setDescription}
      />

      <Input
        label="URI"
        name="uri"
        type="url"
        value={uri}
        placeholder="https://example.org/scheme"
        onChange={setUri}
      />

      <Input
        label="Publisher"
        name="publisher"
        value={publisher}
        placeholder="Organization name"
        onChange={setPublisher}
      />

      <div class="scheme-form__actions">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading || !title.trim()}>
          {loading ? "Saving..." : scheme ? "Save Changes" : "Create Scheme"}
        </Button>
      </div>
    </form>
  );
}
