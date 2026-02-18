import { useState, useEffect } from "preact/hooks";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import {
  publishingApi,
  type PublishPreview,
  type PublishedVersionRead,
} from "../../api/publishing";
import "./PublishModal.css";

interface PublishModalProps {
  isOpen: boolean;
  projectId: string;
  onClose: () => void;
  initialTab?: Tab;
}

type Tab = "publish" | "versions";
type Step = "loading" | "preview" | "form" | "publishing" | "success";

export function PublishModal({
  isOpen,
  projectId,
  onClose,
  initialTab = "publish",
}: PublishModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>(initialTab);
  const [step, setStep] = useState<Step>("loading");
  const [preview, setPreview] = useState<PublishPreview | null>(null);
  const [versions, setVersions] = useState<PublishedVersionRead[]>([]);
  const [draft, setDraft] = useState<PublishedVersionRead | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [version, setVersion] = useState("");
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [publishedVersion, setPublishedVersion] =
    useState<PublishedVersionRead | null>(null);

  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      loadData();
    }
  }, [isOpen]);

  async function loadData() {
    setStep("loading");
    setError(null);

    try {
      const [previewData, versionsData] = await Promise.all([
        publishingApi.getPreview(projectId),
        publishingApi.listVersions(projectId),
      ]);

      setPreview(previewData);
      setVersions(versionsData);

      const existingDraft = versionsData.find((v) => !v.finalized) ?? null;
      setDraft(existingDraft);

      setStep(existingDraft ? "draft" as Step : "preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
      setStep("preview");
    }
  }

  function handleClose() {
    setActiveTab(initialTab);
    setStep("loading");
    setPreview(null);
    setVersions([]);
    setDraft(null);
    setError(null);
    setVersion("");
    setTitle("");
    setNotes("");
    setSubmitting(false);
    setPublishedVersion(null);
    onClose();
  }

  function handleContinue() {
    if (preview?.suggested_version) {
      setVersion(preview.suggested_version);
    }
    setStep("form");
  }

  async function handlePublish(finalized: boolean) {
    setSubmitting(true);
    setError(null);

    try {
      const result = await publishingApi.publish(projectId, {
        version,
        title,
        notes: notes || null,
        finalized,
      });
      setPublishedVersion(result);
      setStep("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Publishing failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFinalize() {
    if (!draft) return;
    setSubmitting(true);
    setError(null);

    try {
      const result = await publishingApi.finalizeVersion(projectId, draft.id);
      setPublishedVersion(result);
      setStep("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Finalization failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDiscard() {
    if (!draft) return;
    setSubmitting(true);
    setError(null);

    try {
      await publishingApi.deleteDraft(projectId, draft.id);
      setDraft(null);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to discard draft");
    } finally {
      setSubmitting(false);
    }
  }

  const isValid = preview?.validation.valid ?? false;
  const versionPattern = /^\d+(\.\d+)*$/;
  const canPublish =
    version.trim() !== "" &&
    versionPattern.test(version) &&
    title.trim() !== "" &&
    !submitting;

  return (
    <Modal
      isOpen={isOpen}
      title="Publishing"
      onClose={handleClose}
      size="wide"
    >
      <div class="publish-modal">
        <div class="publish-modal__tabs" role="tablist">
          <button
            role="tab"
            aria-selected={activeTab === "publish"}
            class={`publish-modal__tab ${activeTab === "publish" ? "publish-modal__tab--active" : ""}`}
            onClick={() => setActiveTab("publish")}
          >
            Publish
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "versions"}
            class={`publish-modal__tab ${activeTab === "versions" ? "publish-modal__tab--active" : ""}`}
            onClick={() => setActiveTab("versions")}
          >
            Versions
          </button>
        </div>

        {activeTab === "publish" && (
          <div class="publish-modal__content">
            {step === "loading" && (
              <div class="publish-modal__loading">Loading...</div>
            )}

            {step === "preview" && preview && (
              <div class="publish-modal__preview">
                {renderContentSummary()}
                {renderValidation()}
                {renderDiff()}

                {error && <p class="publish-modal__error">{error}</p>}

                <div class="publish-modal__actions">
                  <Button variant="secondary" onClick={handleClose}>
                    Cancel
                  </Button>
                  <Button onClick={handleContinue} disabled={!isValid}>
                    Continue
                  </Button>
                </div>
              </div>
            )}

            {step === "form" && (
              <div class="publish-modal__form">
                <div class="publish-modal__field">
                  <label
                    class="publish-modal__label"
                    for="publish-version"
                  >
                    Version <span class="publish-modal__required">*</span>
                  </label>
                  <input
                    id="publish-version"
                    type="text"
                    class="publish-modal__input"
                    value={version}
                    onInput={(e) =>
                      setVersion((e.target as HTMLInputElement).value)
                    }
                    placeholder="e.g. 1.0"
                  />
                </div>

                <div class="publish-modal__field">
                  <label class="publish-modal__label" for="publish-title">
                    Title <span class="publish-modal__required">*</span>
                  </label>
                  <input
                    id="publish-title"
                    type="text"
                    class="publish-modal__input"
                    value={title}
                    onInput={(e) =>
                      setTitle((e.target as HTMLInputElement).value)
                    }
                    placeholder="e.g. Initial release"
                  />
                </div>

                <div class="publish-modal__field">
                  <label class="publish-modal__label" for="publish-notes">
                    Release notes
                  </label>
                  <textarea
                    id="publish-notes"
                    class="publish-modal__input publish-modal__textarea"
                    value={notes}
                    onInput={(e) =>
                      setNotes((e.target as HTMLTextAreaElement).value)
                    }
                    rows={3}
                    placeholder="Optional notes about this version"
                  />
                </div>

                {error && <p class="publish-modal__error">{error}</p>}

                <div class="publish-modal__actions">
                  <Button
                    variant="secondary"
                    onClick={() => handlePublish(false)}
                    disabled={!canPublish}
                  >
                    Save as Draft
                  </Button>
                  <Button
                    onClick={() => handlePublish(true)}
                    disabled={!canPublish}
                  >
                    {submitting ? "Publishing..." : "Publish"}
                  </Button>
                </div>
              </div>
            )}

            {(step as string) === "draft" && draft && preview && (
              <div class="publish-modal__draft">
                <div class="publish-modal__draft-info">
                  <h3 class="publish-modal__draft-heading">
                    Draft: v{draft.version}
                  </h3>
                  <p class="publish-modal__draft-title">{draft.title}</p>
                  {draft.notes && (
                    <p class="publish-modal__draft-notes">{draft.notes}</p>
                  )}
                </div>

                {renderValidation()}

                {error && <p class="publish-modal__error">{error}</p>}

                <div class="publish-modal__actions">
                  <Button
                    variant="danger"
                    onClick={handleDiscard}
                    disabled={submitting}
                  >
                    Discard
                  </Button>
                  <Button
                    onClick={handleFinalize}
                    disabled={!isValid || submitting}
                  >
                    {submitting ? "Finalizing..." : "Finalize"}
                  </Button>
                </div>
              </div>
            )}

            {step === "success" && publishedVersion && (
              <div class="publish-modal__success">
                <p>
                  Version <strong>{publishedVersion.version}</strong> —{" "}
                  {publishedVersion.title} —{" "}
                  {publishedVersion.finalized
                    ? "published successfully."
                    : "saved as draft."}
                </p>
                <div class="publish-modal__actions">
                  <Button onClick={handleClose}>Done</Button>
                </div>
              </div>
            )}

            {step === "preview" && !preview && error && (
              <div class="publish-modal__error-state">
                <p class="publish-modal__error">{error}</p>
                <div class="publish-modal__actions">
                  <Button variant="secondary" onClick={handleClose}>
                    Close
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "versions" && (
          <div class="publish-modal__versions">
            {versions.length === 0 ? (
              <p class="publish-modal__empty">No published versions yet.</p>
            ) : (
              <div class="publish-modal__version-list">
                {versions.map((v) => (
                  <div key={v.id} class="publish-modal__version-row">
                    <span
                      class={`publish-modal__version-badge ${
                        !v.finalized
                          ? "publish-modal__version-badge--draft"
                          : v.latest
                            ? "publish-modal__version-badge--latest"
                            : ""
                      }`}
                    >
                      {v.finalized ? v.version : "Draft"}
                    </span>
                    <div class="publish-modal__version-info">
                      <span class="publish-modal__version-title">
                        {v.title}
                      </span>
                      <span class="publish-modal__version-meta">
                        {v.published_at && formatDate(v.published_at)}
                        {v.publisher && ` by ${v.publisher}`}
                      </span>
                    </div>
                    {v.latest && (
                      <span class="publish-modal__latest-badge">latest</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );

  function renderContentSummary() {
    if (!preview) return null;
    const { content_summary: cs } = preview;
    return (
      <div class="publish-modal__summary">
        <span class="publish-modal__summary-item">
          {cs.schemes} schemes
        </span>
        <span class="publish-modal__summary-item">
          {cs.concepts} concepts
        </span>
        <span class="publish-modal__summary-item">
          {cs.properties} properties
        </span>
      </div>
    );
  }

  function renderValidation() {
    if (!preview) return null;
    const { validation } = preview;

    if (validation.valid) {
      return (
        <div class="publish-modal__validation publish-modal__validation--valid">
          Validation passed
        </div>
      );
    }

    return (
      <div class="publish-modal__validation publish-modal__validation--invalid">
        <p class="publish-modal__validation-heading">Validation errors</p>
        <ul class="publish-modal__validation-errors">
          {validation.errors.map((err, i) => (
            <li key={i} class="publish-modal__validation-error">
              {err.message}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  function renderDiff() {
    if (!preview) return null;
    const { diff } = preview;

    if (!diff) {
      return (
        <div class="publish-modal__diff-empty">
          This will be the first version of this project.
        </div>
      );
    }

    const hasChanges =
      diff.added.length > 0 ||
      diff.modified.length > 0 ||
      diff.removed.length > 0;

    if (!hasChanges) {
      return (
        <div class="publish-modal__diff-empty">No changes since last version.</div>
      );
    }

    return (
      <div class="publish-modal__diff">
        <p class="publish-modal__diff-heading">Changes since last version</p>

        {diff.added.length > 0 && (
          <div class="publish-modal__diff-section">
            <h4 class="publish-modal__diff-section-title publish-modal__diff-section-title--added">
              Added ({diff.added.length})
            </h4>
            {diff.added.map((item, i) => (
              <div key={i} class="publish-modal__diff-item">
                <span class="publish-modal__diff-type">{item.entity_type}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        )}

        {diff.modified.length > 0 && (
          <div class="publish-modal__diff-section">
            <h4 class="publish-modal__diff-section-title publish-modal__diff-section-title--modified">
              Modified ({diff.modified.length})
            </h4>
            {diff.modified.map((item, i) => (
              <div key={i} class="publish-modal__diff-item">
                <span class="publish-modal__diff-type">{item.entity_type}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        )}

        {diff.removed.length > 0 && (
          <div class="publish-modal__diff-section">
            <h4 class="publish-modal__diff-section-title publish-modal__diff-section-title--removed">
              Removed ({diff.removed.length})
            </h4>
            {diff.removed.map((item, i) => (
              <div key={i} class="publish-modal__diff-item">
                <span class="publish-modal__diff-type">{item.entity_type}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
