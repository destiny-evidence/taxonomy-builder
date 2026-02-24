import { useState, useEffect } from "preact/hooks";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { Input } from "../common/Input";
import {
  publishingApi,
  type PublishPreview,
  type PublishedVersionRead,
} from "../../api/publishing";
import { FEEDBACK_URL } from "../../config";
import { projectsApi } from "../../api/projects";
import type { ExportFormat } from "../../api/schemes";
import "./PublishModal.css";

interface PublishModalProps {
  isOpen: boolean;
  projectId: string;
  onClose: () => void;
  initialTab?: Tab;
}

type Tab = "publish" | "versions";
type Step = "loading" | "preview" | "confirm" | "publishing" | "success";

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
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [version, setVersion] = useState("");
  const [preRelease, setPreRelease] = useState(false);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [publishedVersion, setPublishedVersion] =
    useState<PublishedVersionRead | null>(null);
  const [copied, setCopied] = useState(false);
  const [exportingVersionId, setExportingVersionId] = useState<string | null>(null);
  const [exportPickerVersionId, setExportPickerVersionId] = useState<string | null>(null);

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
      setVersion(previewData.suggested_version ?? "");
      setStep("preview");
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
    setError(null);
    setVersion("");
    setPreRelease(false);
    setTitle("");
    setNotes("");
    setSubmitting(false);
    setPublishedVersion(null);
    setExportingVersionId(null);
    setExportPickerVersionId(null);
    onClose();
  }

  async function handleExportVersion(v: PublishedVersionRead, format: ExportFormat) {
    setExportingVersionId(v.id);
    setExportPickerVersionId(null);
    try {
      const { blob, filename } = await projectsApi.exportVersion(projectId, v.version, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      if (filename) a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setExportingVersionId(null);
    }
  }

  async function handlePublish() {
    if (!version.trim()) return;
    setSubmitting(true);
    setError(null);

    try {
      const result = await publishingApi.publish(projectId, {
        version,
        title,
        notes: notes || null,
        pre_release: preRelease,
      });
      setPublishedVersion(result);
      setStep("success");
      // Refresh version list so the Versions tab is up to date
      publishingApi.listVersions(projectId).then(setVersions).catch(() => {});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Publishing failed");
    } finally {
      setSubmitting(false);
    }
  }

  const isValid = preview?.validation.valid ?? false;
  const RELEASE_PATTERN = /^\d+(\.\d+)+$/;
  const PRE_RELEASE_PATTERN = /^\d+(\.\d+)+-pre\d+$/;
  const versionPattern = preRelease ? PRE_RELEASE_PATTERN : RELEASE_PATTERN;
  const versionFormatValid =
    version.trim() === "" || versionPattern.test(version.trim());
  const canPublish =
    isValid &&
    version.trim() !== "" &&
    versionFormatValid &&
    title.trim() !== "" &&
    !submitting;

  return (
    <Modal isOpen={isOpen} title="Publishing" onClose={handleClose} size="wide">
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

                {isValid && (
                  <div class="publish-modal__form">
                    <div class="publish-modal__checkbox-row">
                      <label class="publish-modal__checkbox-label">
                        <input
                          type="checkbox"
                          checked={preRelease}
                          onChange={(e) => {
                            const checked = (e.target as HTMLInputElement)
                              .checked;
                            setPreRelease(checked);
                            setVersion(
                              checked
                                ? (preview?.suggested_pre_release_version ?? "")
                                : (preview?.suggested_version ?? ""),
                            );
                          }}
                        />
                        Pre-release
                      </label>
                      <span
                        class="publish-modal__info-icon"
                        aria-label="More information about pre-releases"
                      >
                        &#9432;
                        <span class="publish-modal__tooltip">
                          Pre-release versions can be exported and shared for
                          feedback, but are not formal releases of vocabularies
                          and cannot be mapped to other vocabularies.
                        </span>
                      </span>
                    </div>

                    <div class="input-field">
                      <label class="input-field__label" for="publish-version">
                        Version
                      </label>
                      <input
                        id="publish-version"
                        type="text"
                        class="input-field__input publish-modal__version-input"
                        value={version}
                        onInput={(e) =>
                          setVersion((e.target as HTMLInputElement).value)
                        }
                      />
                      {!versionFormatValid && (
                        <span class="input-field__error">
                          {preRelease
                            ? "Version must be like 2.0-pre1"
                            : "Version must be like 1.0 or 2.1.3"}
                        </span>
                      )}
                      {(preview.latest_version ||
                        preview.latest_pre_release_version) && (
                        <span class="publish-modal__version-hint">
                          Recent:{" "}
                          {[
                            preview.latest_pre_release_version,
                            preview.latest_version,
                          ]
                            .filter(Boolean)
                            .join(", ")}
                        </span>
                      )}
                    </div>

                    <Input
                      label="Title"
                      name="publish-title"
                      value={title}
                      onChange={setTitle}
                      placeholder="e.g. Initial release"
                      required
                    />

                    <Input
                      label="Release notes"
                      name="publish-notes"
                      value={notes}
                      onChange={setNotes}
                      placeholder="Optional notes about this version"
                      multiline
                      rows={3}
                    />
                  </div>
                )}

                {error && <p class="publish-modal__error">{error}</p>}

                <div class="publish-modal__actions">
                  <Button variant="secondary" onClick={handleClose}>
                    Cancel
                  </Button>
                  <Button
                    onClick={() => setStep("confirm")}
                    disabled={!canPublish}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}

            {step === "confirm" && (
              <div class="publish-modal__confirm">
                <p>
                  You are about to publish {preRelease ? "pre-release " : ""}
                  version <strong>{version}</strong> — {title}.
                </p>
                <p class="publish-modal__confirm-warning">
                  Published versions are immutable and cannot be changed.
                </p>
                {error && <p class="publish-modal__error">{error}</p>}
                <div class="publish-modal__actions">
                  <Button
                    variant="secondary"
                    onClick={() => setStep("preview")}
                  >
                    Back
                  </Button>
                  <Button onClick={handlePublish} disabled={submitting}>
                    {submitting ? "Publishing..." : "Publish"}
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
                    : "published as pre-release."}
                </p>
                {FEEDBACK_URL && (() => {
                  const permalink = `${FEEDBACK_URL}/${projectId}/${publishedVersion.version}`;
                  return (
                    <div class="publish-modal__permalink">
                      <a href={permalink} target="_blank" rel="noopener noreferrer">
                        {permalink}
                      </a>
                      <button
                        class="publish-modal__copy-btn"
                        onClick={() => {
                          navigator.clipboard.writeText(permalink);
                          setCopied(true);
                          setTimeout(() => setCopied(false), 2000);
                        }}
                      >
                        {copied ? "Copied!" : "Copy"}
                      </button>
                    </div>
                  );
                })()}
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
                          ? "publish-modal__version-badge--pre-release"
                          : v.latest
                            ? "publish-modal__version-badge--latest"
                            : ""
                      }`}
                    >
                      {v.version}
                    </span>
                    <div class="publish-modal__version-info">
                      <span class="publish-modal__version-title">
                        {v.title}
                      </span>
                      {v.notes && (
                        <span class="publish-modal__version-notes">
                          {v.notes}
                        </span>
                      )}
                      <span class="publish-modal__version-meta">
                        {v.published_at && formatDate(v.published_at)}
                        {v.publisher && ` by ${v.publisher}`}
                      </span>
                    </div>
                    {v.latest && (
                      <span class="publish-modal__status-badge publish-modal__status-badge--latest">latest</span>
                    )}
                    {!v.finalized && (
                      <span class="publish-modal__status-badge publish-modal__status-badge--pre-release">
                        pre-release
                      </span>
                    )}
                    {exportingVersionId === v.id ? (
                      <span class="publish-modal__export-status">Exporting…</span>
                    ) : exportPickerVersionId === v.id ? (
                      <div class="publish-modal__export-picker">
                        <Button size="sm" variant="secondary" onClick={() => handleExportVersion(v, "ttl")}>
                          Turtle
                        </Button>
                        <Button size="sm" variant="secondary" onClick={() => handleExportVersion(v, "xml")}>
                          RDF/XML
                        </Button>
                        <Button size="sm" variant="secondary" onClick={() => handleExportVersion(v, "jsonld")}>
                          JSON-LD
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setExportPickerVersionId(null)}>
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setExportPickerVersionId(v.id)}
                      >
                        Export
                      </Button>
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
        <span class="publish-modal__summary-item">{cs.schemes} schemes</span>
        <span class="publish-modal__summary-item">{cs.concepts} concepts</span>
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
          This will be the first released version of this project.
        </div>
      );
    }

    const hasChanges =
      diff.added.length > 0 ||
      diff.modified.length > 0 ||
      diff.removed.length > 0;

    if (!hasChanges) {
      return (
        <div class="publish-modal__diff-empty">
          No changes since last released version.
        </div>
      );
    }

    return (
      <div class="publish-modal__diff">
        <p class="publish-modal__diff-heading">
          Changes since last released version
        </p>

        {diff.added.length > 0 && (
          <details class="publish-modal__diff-section">
            <summary class="publish-modal__diff-section-title publish-modal__diff-section-title--added">
              Added ({diff.added.length}): {formatGroupedCount(diff.added)}
            </summary>
            <div class="publish-modal__diff-items">
              {diff.added.map((item, i) => (
                <div key={i} class="publish-modal__diff-item">
                  <span class="publish-modal__diff-type">
                    {item.entity_type}
                  </span>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </details>
        )}

        {diff.modified.length > 0 && (
          <details class="publish-modal__diff-section">
            <summary class="publish-modal__diff-section-title publish-modal__diff-section-title--modified">
              Modified ({diff.modified.length}):{" "}
              {formatGroupedCount(diff.modified)}
            </summary>
            <div class="publish-modal__diff-items">
              {diff.modified.map((item, i) => (
                <div
                  key={i}
                  class="publish-modal__diff-item publish-modal__diff-item--modified"
                >
                  <div class="publish-modal__diff-item-header">
                    <span class="publish-modal__diff-type">
                      {item.entity_type}
                    </span>
                    <span>{item.label}</span>
                  </div>
                  {item.changes.length > 0 && (
                    <div class="publish-modal__field-changes">
                      {item.changes.map((change, j) => (
                        <div key={j} class="publish-modal__field-change">
                          <span class="publish-modal__field-name">
                            {change.field}
                          </span>
                          <span class="publish-modal__field-old">
                            {change.old ?? "(empty)"}
                          </span>
                          <span class="publish-modal__field-arrow">
                            {"\u2192"}
                          </span>
                          <span class="publish-modal__field-new">
                            {change.new ?? "(empty)"}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </details>
        )}

        {diff.removed.length > 0 && (
          <details class="publish-modal__diff-section">
            <summary class="publish-modal__diff-section-title publish-modal__diff-section-title--removed">
              Removed ({diff.removed.length}):{" "}
              {formatGroupedCount(diff.removed)}
            </summary>
            <div class="publish-modal__diff-items">
              {diff.removed.map((item, i) => (
                <div key={i} class="publish-modal__diff-item">
                  <span class="publish-modal__diff-type">
                    {item.entity_type}
                  </span>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </details>
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

function formatGroupedCount(items: Array<{ entity_type: string }>): string {
  const counts = new Map<string, number>();
  for (const item of items) {
    counts.set(item.entity_type, (counts.get(item.entity_type) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([type, count]) => {
      const plural = type.endsWith("s") ? type + "es" : type + "s";
      return `${count} ${count === 1 ? type : plural}`;
    })
    .join(", ");
}
