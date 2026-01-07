import { useEffect, useState } from "preact/hooks";
import { listVersions } from "../../api/versions";
import { Button } from "../common/Button";
import { PublishDialog } from "./PublishDialog";
import type { PublishedVersion } from "../../types/models";
import "./VersionsPanel.css";

interface VersionsPanelProps {
  schemeId: string;
}

export function VersionsPanel({ schemeId }: VersionsPanelProps) {
  const [versions, setVersions] = useState<PublishedVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPublishDialog, setShowPublishDialog] = useState(false);

  async function fetchVersions() {
    try {
      setLoading(true);
      setError(null);
      const data = await listVersions(schemeId);
      setVersions(data);
    } catch (err) {
      setError("Failed to load versions");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchVersions();
  }, [schemeId]);

  function handleExport(versionId: string) {
    window.open(`/api/versions/${versionId}/export`, "_blank");
  }

  function handlePublished() {
    fetchVersions();
  }

  if (loading) {
    return (
      <div class="versions-panel">
        <div class="versions-panel__loading">Loading versions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div class="versions-panel">
        <div class="versions-panel__error">Error: {error}</div>
        <Button size="sm" onClick={() => setShowPublishDialog(true)}>
          Publish New Version
        </Button>
        <PublishDialog
          isOpen={showPublishDialog}
          schemeId={schemeId}
          onClose={() => setShowPublishDialog(false)}
          onPublished={handlePublished}
        />
      </div>
    );
  }

  if (versions.length === 0) {
    return (
      <div class="versions-panel">
        <div class="versions-panel__empty">No versions published yet.</div>
        <Button size="sm" onClick={() => setShowPublishDialog(true)}>
          Publish New Version
        </Button>
        <PublishDialog
          isOpen={showPublishDialog}
          schemeId={schemeId}
          onClose={() => setShowPublishDialog(false)}
          onPublished={handlePublished}
        />
      </div>
    );
  }

  return (
    <div class="versions-panel">
      <div class="versions-panel__header">
        <h3 class="versions-panel__title">Published Versions</h3>
        <Button size="sm" onClick={() => setShowPublishDialog(true)}>
          Publish New Version
        </Button>
      </div>
      <ul class="versions-panel__list">
        {versions.map((version) => (
          <li key={version.id} class="versions-panel__item">
            <div class="versions-panel__item-header">
              <span class="versions-panel__version-label">
                v{version.version_label}
              </span>
              <span class="versions-panel__published-at">
                {new Date(version.published_at).toLocaleDateString()}
              </span>
            </div>
            {version.notes && (
              <div class="versions-panel__notes">{version.notes}</div>
            )}
            <div class="versions-panel__actions">
              <Button
                variant="secondary"
                onClick={() => handleExport(version.id)}
              >
                Export
              </Button>
            </div>
          </li>
        ))}
      </ul>
      <PublishDialog
        isOpen={showPublishDialog}
        schemeId={schemeId}
        onClose={() => setShowPublishDialog(false)}
        onPublished={handlePublished}
      />
    </div>
  );
}
