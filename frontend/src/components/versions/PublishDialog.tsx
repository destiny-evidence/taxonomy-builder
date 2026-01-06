import { useState } from "preact/hooks";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { publishVersion } from "../../api/versions";

interface PublishDialogProps {
  isOpen: boolean;
  schemeId: string;
  onClose: () => void;
  onPublished: () => void;
}

export function PublishDialog({
  isOpen,
  schemeId,
  onClose,
  onPublished,
}: PublishDialogProps) {
  const [versionLabel, setVersionLabel] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await publishVersion(schemeId, {
        version_label: versionLabel,
        notes: notes || undefined,
      });
      onPublished();
      onClose();
    } catch (err) {
      setError("Failed to publish version");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal isOpen={isOpen} title="Publish Version" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="version-label">Version Label</label>
          <input
            id="version-label"
            type="text"
            value={versionLabel}
            onInput={(e) => setVersionLabel((e.target as HTMLInputElement).value)}
            placeholder="e.g., 1.0, 2.0"
          />
        </div>

        <div>
          <label htmlFor="version-notes">Notes</label>
          <textarea
            id="version-notes"
            value={notes}
            onInput={(e) => setNotes((e.target as HTMLTextAreaElement).value)}
            placeholder="Optional release notes"
          />
        </div>

        {error && <div className="error">{error}</div>}

        <div>
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={!versionLabel.trim() || submitting}
          >
            Publish
          </Button>
        </div>
      </form>
    </Modal>
  );
}
