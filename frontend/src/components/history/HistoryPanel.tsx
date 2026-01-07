import { useEffect, useState } from "preact/hooks";
import type { JSX } from "preact";
import { getSchemeHistory } from "../../api/history";
import { getActionLabel, getEntityTypeLabel } from "./historyStrings";
import type { ChangeEvent } from "../../types/models";
import "./HistoryPanel.css";

interface HistoryPanelProps {
  schemeId: string;
  refreshKey?: number;
}

/**
 * Render a human-readable description of what changed.
 */
function ChangeDescription({ event }: { event: ChangeEvent }): JSX.Element | null {
  const afterState = event.after_state as Record<string, unknown> | null;
  const beforeState = event.before_state as Record<string, unknown> | null;

  // For concepts, show the pref_label in bold
  if (event.entity_type === "concept") {
    const label = afterState?.pref_label || beforeState?.pref_label;
    if (label && typeof label === "string") {
      return <strong>{label}</strong>;
    }
  }

  // For broader relationships, show concept → broader
  if (event.entity_type === "concept_broader") {
    const conceptLabel = afterState?.concept_label || beforeState?.concept_label;
    const broaderLabel = afterState?.broader_label || beforeState?.broader_label;
    if (conceptLabel && broaderLabel) {
      return (
        <>
          <strong>{conceptLabel as string}</strong>
          {" → "}
          <strong>{broaderLabel as string}</strong>
        </>
      );
    }
  }

  // For related relationships, show concept ↔ related
  if (event.entity_type === "concept_related") {
    const conceptLabel = afterState?.concept_label || beforeState?.concept_label;
    const relatedLabel = afterState?.related_label || beforeState?.related_label;
    if (conceptLabel && relatedLabel) {
      return (
        <>
          <strong>{conceptLabel as string}</strong>
          {" ↔ "}
          <strong>{relatedLabel as string}</strong>
        </>
      );
    }
  }

  // For published versions, show version label
  const versionLabel = afterState?.version_label || beforeState?.version_label;
  if (versionLabel && typeof versionLabel === "string") {
    return <>v{versionLabel}</>;
  }

  return null;
}

/**
 * Format a timestamp for display.
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) {
    return "Just now";
  }
  if (diffMins < 60) {
    return `${diffMins}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`;
  }
  return date.toLocaleDateString();
}

export function HistoryPanel({ schemeId, refreshKey }: HistoryPanelProps) {
  const [history, setHistory] = useState<ChangeEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        setLoading(true);
        setError(null);
        const data = await getSchemeHistory(schemeId);
        setHistory(data);
      } catch (err) {
        setError("Failed to load history");
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [schemeId, refreshKey]);

  if (loading) {
    return (
      <div class="history-panel">
        <div class="history-panel__loading">Loading history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div class="history-panel">
        <div class="history-panel__error">Error: {error}</div>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div class="history-panel">
        <div class="history-panel__empty">No history available.</div>
      </div>
    );
  }

  return (
    <div class="history-panel">
      <div class="history-panel__list">
        {history.map((event) => {
          const hasDetails = event.before_state || event.after_state;
          return (
            <div key={event.id} class="history-panel__item">
              <div class="history-panel__item-header">
                <span class={`history-panel__action history-panel__action--${event.action}`}>
                  {getActionLabel(event.action)}
                </span>
                <span class="history-panel__entity-type">
                  {getEntityTypeLabel(event.entity_type)}
                </span>
              </div>
              <div class="history-panel__description">
                <ChangeDescription event={event} />
              </div>
              <div class="history-panel__timestamp">
                {formatTimestamp(event.timestamp)}
              </div>
              {hasDetails && (
                <details class="history-panel__details">
                  <summary>View changes</summary>
                  <div class="history-panel__diff">
                    {event.before_state && (
                      <div class="history-panel__before">
                        <span class="history-panel__diff-label">Before:</span>
                        <pre>{JSON.stringify(event.before_state, null, 2)}</pre>
                      </div>
                    )}
                    {event.after_state && (
                      <div class="history-panel__after">
                        <span class="history-panel__diff-label">After:</span>
                        <pre>{JSON.stringify(event.after_state, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                </details>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
