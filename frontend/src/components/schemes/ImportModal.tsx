import { useState } from "preact/hooks";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import {
  schemesApi,
  type ImportPreview,
  type ImportResult,
} from "../../api/schemes";
import "./ImportModal.css";

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
    // Reset state
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

            {preview.warnings.length > 0 && (
              <div class="import-modal__warnings">
                <p class="import-modal__warning-summary">
                  {preview.warnings.length} warning{preview.warnings.length !== 1 ? "s" : ""}:
                  {preview.warnings.length <= 5
                    ? ""
                    : ` showing first 5 of ${preview.warnings.length}`}
                </p>
                {preview.warnings.slice(0, 5).map((w, i) => (
                  <p key={i} class="import-modal__warning">{w}</p>
                ))}
              </div>
            )}

            {error && <p class="import-modal__error">{error}</p>}

            <div class="import-modal__actions">
              <Button variant="secondary" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleImport}>Import All</Button>
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
            <p>
              {(() => {
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
              })()}
            </p>
            {result.warnings.length > 0 && (
              <p class="import-modal__warning-summary">
                {result.warnings.length} property range{result.warnings.length !== 1 ? "s" : ""} could
                not be resolved.
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
