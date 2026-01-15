import { useEffect, useState } from "preact/hooks";
import { route } from "preact-router";
import { schemesApi } from "../api/schemes";
import "./SchemeDetailPage.css";

interface SchemeDetailPageProps {
  path?: string;
  schemeId?: string;
}

/**
 * Legacy route handler that redirects /schemes/:id to /projects/:projectId/schemes/:id
 */
export function SchemeDetailPage({ schemeId }: SchemeDetailPageProps) {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (schemeId) {
      schemesApi
        .get(schemeId)
        .then((scheme) => {
          route(`/projects/${scheme.project_id}/schemes/${schemeId}`, true);
        })
        .catch(() => {
          setError("Scheme not found");
        });
    }
  }, [schemeId]);

  if (error) {
    return <div class="scheme-detail__error">{error}</div>;
  }

  return <div class="scheme-detail__loading">Redirecting...</div>;
}
