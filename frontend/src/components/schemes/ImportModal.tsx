import { useState } from "preact/hooks";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import {
  schemesApi,
  type ImportPreview,
  type ImportResult,
  type ValidationIssue,
} from "../../api/schemes";
import "./ImportModal.css";

function formatImportSummary(result: ImportResult): string {
  const parts = [
    result.classes_created.length > 0 &&
      `${result.classes_created.length} classes`,
    result.properties_created.length > 0 &&
      `${result.properties_created.length} properties`,
    result.schemes_created.length > 0 &&
      `${result.schemes_created.length} schemes with ${result.total_concepts_created} concepts and ${result.total_relationships_created} relationships`,
  ].filter(Boolean);
  return parts.length > 0
    ? `Successfully imported ${parts.join(", ")}.`
    : "No entities found in file.";
}

function groupByType(issues: ValidationIssue[]): Map<string, ValidationIssue[]> {
  const groups = new Map<string, ValidationIssue[]>();
  for (const issue of issues) {
    const existing = groups.get(issue.type);
    if (existing) {
      existing.push(issue);
    } else {
      groups.set(issue.type, [issue]);
    }
  }
  return groups;
}

function ValidationIssueGroup({
  issues,
  severity,
}: {
  issues: ValidationIssue[];
  severity: "error" | "warning" | "info";
}) {
  const grouped = groupByType(issues);
  if (grouped.size === 0) return null;

  const prefix = severity === "error" ? "Error" : severity === "warning" ? "Warning" : "Note";
  const cssClass = `import-modal__validation-${severity}`;

  return (
    <div class={cssClass}>
      {[...grouped.entries()].map(([type, group]) => (
        <p key={type} class="import-modal__validation-item">
          <strong>{prefix}:</strong>{" "}
          {group.length > 1
            ? `${group[0].message} (+${group.length - 1} more)`
            : group[0].message}
        </p>
      ))}
    </div>
  );
}

function ValidationIssues({
  issues,
}: {
  issues: ValidationIssue[];
}) {
  if (!issues || issues.length === 0) return null;

  const errors = issues.filter((i) => i.severity === "error");
  const warnings = issues.filter((i) => i.severity === "warning");
  const infos = issues.filter((i) => i.severity === "info");

  const [showInfo, setShowInfo] = useState(false);

  return (
    <div class="import-modal__validation" aria-live="polite">
      <ValidationIssueGroup issues={errors} severity="error" />
      <ValidationIssueGroup issues={warnings} severity="warning" />
      {infos.length > 0 && (
        <div class="import-modal__validation-info-section">
          <button
            type="button"
            class="import-modal__validation-info-toggle"
            onClick={() => setShowInfo(!showInfo)}
          >
            {showInfo ? "Hide" : "Show"} {infos.length} informational note
            {infos.length !== 1 ? "s" : ""}
          </button>
          {showInfo && <ValidationIssueGroup issues={infos} severity="info" />}
        </div>
      )}
    </div>
  );
}

interface ImportModalProps {
  isOpen: boolean;
  projectId: string;
  onClose: () => void;
  onSuccess: () => void;
}

type Step = "select" | "preview" | "importing" | "success";

export function ImportModal({
  isOpen,
  projectId,
  onClose,
  onSuccess,
}: ImportModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [step, setStep] = useState<Step>("select");
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function handleFileChange(e: Event) {
    const target = e.target as HTMLInputElement;
    const selectedFile = target.files?.[0] ?? null;
    setFile(selectedFile);
    setError(null);
  }

  async function handlePreview() {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const previewData = await schemesApi.previewImport(projectId, file);
      setPreview(previewData);
      setStep("preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to parse file");
    } finally {
      setLoading(false);
    }
  }

  async function handleImport() {
    if (!file) return;

    setStep("importing");
    setError(null);

    try {
      const importResult = await schemesApi.executeImport(projectId, file);
      setResult(importResult);
      setStep("success");
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
      setStep("preview");
    }
  }

  function handleClose() {
    setFile(null);
    setStep("select");
    setPreview(null);
    setResult(null);
    setError(null);
    setLoading(false);
    onClose();
  }

  return (
    <Modal isOpen={isOpen} title="Import" onClose={handleClose}>
      <div class="import-modal">
        {step === "select" && (
          <div class="import-modal__select">
            <label class="import-modal__file-label">
              Select RDF file
              <input
                type="file"
                accept=".ttl,.rdf,.xml,.jsonld,.json,.nt,.n3,.owl,.turtle"
                onChange={handleFileChange}
                class="import-modal__file-input"
              />
            </label>
            <p class="import-modal__formats">
              Supported formats: .ttl, .rdf, .jsonld, .nt
            </p>

            {error && <p class="import-modal__error">{error}</p>}

            <div class="import-modal__actions">
              <Button variant="secondary" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handlePreview} disabled={!file || loading}>
                {loading ? "Parsing..." : "Preview"}
              </Button>
            </div>
          </div>
        )}

        {step === "preview" && preview && (
          <div class="import-modal__preview">
            <ValidationIssues issues={preview.validation_issues} />

            {preview.valid && (
              <>
                <div class="import-modal__schemes">
                  {preview.schemes.map((scheme, index) => (
                    <div key={index} class="import-modal__scheme-card">
                      <h3 class="import-modal__scheme-title">{scheme.title}</h3>
                      {scheme.description && (
                        <p class="import-modal__scheme-description">
                          {scheme.description}
                        </p>
                      )}
                      {scheme.uri && (
                        <p class="import-modal__scheme-uri">{scheme.uri}</p>
                      )}
                      <div class="import-modal__scheme-stats">
                        <span>{scheme.concepts_count} concepts</span>
                        <span>{scheme.relationships_count} relationships</span>
                      </div>
                      {scheme.warnings.length > 0 && (
                        <div class="import-modal__scheme-warnings">
                          {scheme.warnings.map((warning, i) => (
                            <p key={i} class="import-modal__warning">
                              {warning}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div class="import-modal__totals">
                  <span>
                    Total:{" "}
                    {[
                      preview.classes_count > 0 &&
                        `${preview.classes_count} classes`,
                      preview.properties_count > 0 &&
                        `${preview.properties_count} properties`,
                      `${preview.total_concepts_count} concepts`,
                      `${preview.total_relationships_count} relationships`,
                    ]
                      .filter(Boolean)
                      .join(", ")}
                  </span>
                </div>

                {preview.warnings.length > 0 &&
                  preview.validation_issues.length === 0 && (
                    <div class="import-modal__warnings">
                      <p class="import-modal__warning-summary">
                        {preview.warnings.length} warning
                        {preview.warnings.length !== 1 ? "s" : ""}:
                        {preview.warnings.length <= 5
                          ? ""
                          : ` showing first 5 of ${preview.warnings.length}`}
                      </p>
                      {preview.warnings.slice(0, 5).map((w, i) => (
                        <p key={i} class="import-modal__warning">
                          {w}
                        </p>
                      ))}
                    </div>
                  )}
              </>
            )}

            {error && <p class="import-modal__error">{error}</p>}

            <div class="import-modal__actions">
              <Button variant="secondary" onClick={handleClose}>
                Cancel
              </Button>
              {preview.valid && (
                <Button onClick={handleImport}>Import All</Button>
              )}
            </div>
          </div>
        )}

        {step === "importing" && (
          <div class="import-modal__importing">
            <p>Importing...</p>
          </div>
        )}

        {step === "success" && result && (
          <div class="import-modal__success">
            <p>{formatImportSummary(result)}</p>
            <ValidationIssues issues={result.validation_issues} />
            {result.warnings.length > 0 && (
              <p class="import-modal__warning-summary">
                {result.warnings.length} warning
                {result.warnings.length !== 1 ? "s" : ""} during import.
              </p>
            )}
            <div class="import-modal__actions">
              <Button onClick={handleClose}>Done</Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
