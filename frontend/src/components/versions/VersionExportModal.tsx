import { useState } from "preact/hooks";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { getVersionExportUrl, type ExportFormat } from "../../api/versions";
import "../schemes/ExportModal.css";

interface VersionExportModalProps {
  isOpen: boolean;
  versionId: string;
  versionLabel: string;
  onClose: () => void;
}

const FORMAT_OPTIONS: { value: ExportFormat; label: string; description: string }[] = [
  { value: "ttl", label: "Turtle (.ttl)", description: "Human-readable format" },
  { value: "xml", label: "RDF/XML (.rdf)", description: "Widest compatibility" },
  { value: "jsonld", label: "JSON-LD (.jsonld)", description: "Web-friendly JSON" },
];

export function VersionExportModal({ isOpen, versionId, versionLabel, onClose }: VersionExportModalProps) {
  const [format, setFormat] = useState<ExportFormat>("ttl");

  function handleDownload() {
    const url = getVersionExportUrl(versionId, format);
    window.open(url, "_blank");
    onClose();
  }

  return (
    <Modal isOpen={isOpen} title="Export Version" onClose={onClose}>
      <div class="export-modal">
        <p class="export-modal__description">
          Export version <strong>v{versionLabel}</strong> as SKOS RDF
        </p>

        <div class="export-modal__formats">
          <label class="export-modal__label">Format</label>
          {FORMAT_OPTIONS.map((option) => (
            <label key={option.value} class="export-modal__option">
              <input
                type="radio"
                name="format"
                value={option.value}
                checked={format === option.value}
                onChange={() => setFormat(option.value)}
              />
              <span class="export-modal__option-content">
                <span class="export-modal__option-label">{option.label}</span>
                <span class="export-modal__option-description">{option.description}</span>
              </span>
            </label>
          ))}
        </div>

        <div class="export-modal__actions">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleDownload}>
            Download
          </Button>
        </div>
      </div>
    </Modal>
  );
}
