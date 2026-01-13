import { useState } from "preact/hooks";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import { publishVersion } from "../../api/versions";
import "./PublishDialog.css";

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
      <form class="publish-dialog" onSubmit={handleSubmit}>
        {error && <div class="publish-dialog__error">{error}</div>}

        <Input
          label="Version Label"
          name="version-label"
          value={versionLabel}
          placeholder="e.g., 1.0, 2.0"
          required
          onChange={setVersionLabel}
        />

        <Input
          label="Notes"
          name="version-notes"
          value={notes}
          placeholder="Optional release notes"
          multiline
          onChange={setNotes}
        />

        <div class="publish-dialog__actions">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={!versionLabel.trim() || submitting}
          >
            {submitting ? "Publishing..." : "Publish"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
