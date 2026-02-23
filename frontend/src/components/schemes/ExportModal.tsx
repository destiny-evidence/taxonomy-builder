import { useState } from "preact/hooks";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { schemesApi, type ExportFormat } from "../../api/schemes";
import "./ExportModal.css";

interface ExportModalProps {
  isOpen: boolean;
  schemeId: string;
  schemeTitle: string;
  onClose: () => void;
}

const FORMAT_OPTIONS: { value: ExportFormat; label: string; description: string }[] = [
  { value: "ttl", label: "Turtle (.ttl)", description: "Human-readable format" },
  { value: "xml", label: "RDF/XML (.rdf)", description: "Widest compatibility" },
  { value: "jsonld", label: "JSON-LD (.jsonld)", description: "Web-friendly JSON" },
];

const FORMAT_EXTENSIONS: Record<ExportFormat, string> = {
  ttl: ".ttl",
  xml: ".rdf",
  jsonld: ".jsonld",
};

export function ExportModal({ isOpen, schemeId, schemeTitle, onClose }: ExportModalProps) {
  const [format, setFormat] = useState<ExportFormat>("ttl");
  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    setDownloading(true);
    try {
      const blob = await schemesApi.exportScheme(schemeId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${schemeTitle}${FORMAT_EXTENSIONS[format]}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      onClose();
    } finally {
      setDownloading(false);
    }
  }

  return (
    <Modal isOpen={isOpen} title="Export Scheme" onClose={onClose}>
      <div class="export-modal">
        <p class="export-modal__description">
          Export <strong>{schemeTitle}</strong> as SKOS RDF
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
          <Button onClick={handleDownload} disabled={downloading}>
            {downloading ? "Downloading…" : "Download"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
