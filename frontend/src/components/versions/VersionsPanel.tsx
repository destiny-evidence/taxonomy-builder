import { useEffect, useState } from "preact/hooks";
import { listVersions } from "../../api/versions";
import { Button } from "../common/Button";
import { PublishDialog } from "./PublishDialog";
import type { PublishedVersion } from "../../types/models";

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
    return <div>Loading versions...</div>;
  }

  if (error) {
    return (
      <div>
        <div>Error: {error}</div>
        <Button onClick={() => setShowPublishDialog(true)}>
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
      <div>
        <div>No versions published yet.</div>
        <Button onClick={() => setShowPublishDialog(true)}>
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
    <div className="versions-panel">
      <h3>Published Versions</h3>
      <Button onClick={() => setShowPublishDialog(true)}>
        Publish New Version
      </Button>
      <ul>
        {versions.map((version) => (
          <li key={version.id}>
            <span className="version-label">{version.version_label}</span>
            <span className="published-at">
              {new Date(version.published_at).toLocaleString()}
            </span>
            {version.notes && (
              <span className="notes">{version.notes}</span>
            )}
            <Button
              variant="secondary"
              onClick={() => handleExport(version.id)}
            >
              Export
            </Button>
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
