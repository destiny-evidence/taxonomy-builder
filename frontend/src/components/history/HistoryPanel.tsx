import { useEffect, useMemo, useState } from "preact/hooks";
import type { JSX } from "preact";
import { getSchemeHistory, getProjectHistory } from "../../api/history";
import { getActionLabel, getEntityTypeLabel } from "./historyStrings";
import { HISTORY_FILTERS, getAllowedEntityTypes } from "./historyFilters";
import type { ChangeEvent } from "../../types/models";
import "./HistoryPanel.css";

export type HistorySource =
  | { type: "scheme"; id: string }
  | { type: "project"; id: string };

interface HistoryPanelProps {
  source: HistorySource;
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

  // For properties, show label
  if (event.entity_type === "property") {
    const label = afterState?.label || beforeState?.label;
    if (label && typeof label === "string") {
      return <strong>{label}</strong>;
    }
  }

  // For projects, show name
  if (event.entity_type === "project") {
    const name = afterState?.name || beforeState?.name;
    if (name && typeof name === "string") {
      return <strong>{name}</strong>;
    }
  }

  // For concept schemes, show title
  if (event.entity_type === "concept_scheme") {
    const title = afterState?.title || beforeState?.title;
    if (title && typeof title === "string") {
      return <strong>{title}</strong>;
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

export function HistoryPanel({ source, refreshKey }: HistoryPanelProps) {
  const [history, setHistory] = useState<ChangeEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilters, setSelectedFilters] = useState<Set<string>>(new Set());

  useEffect(() => {
    async function fetchHistory() {
      try {
        setLoading(true);
        setError(null);
        const data =
          source.type === "scheme"
            ? await getSchemeHistory(source.id)
            : await getProjectHistory(source.id);
        setHistory(data);
      } catch (err) {
        setError("Failed to load history");
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [source.type, source.id, refreshKey]);

  const relevantFilters = useMemo(
    () => HISTORY_FILTERS.filter((f) => history.some((e) => f.types.includes(e.entity_type))),
    [history],
  );

  const filteredHistory = useMemo(() => {
    const allowed = getAllowedEntityTypes(selectedFilters);
    if (!allowed) return history;
    return history.filter((e) => allowed.has(e.entity_type));
  }, [history, selectedFilters]);

  function toggleFilter(key: string) {
    setSelectedFilters((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

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

  const filterSummary =
    selectedFilters.size === 0
      ? "Filter: All changes"
      : `Filter: ${[...selectedFilters].map((k) => relevantFilters.find((f) => f.key === k)?.label).filter(Boolean).join(", ")}`;

  return (
    <div class="history-panel">
      {relevantFilters.length > 1 && (
        <details class="history-panel__filters">
          <summary class="history-panel__filters-summary">{filterSummary}</summary>
          <div class="history-panel__filters-options">
            {relevantFilters.map((f) => (
              <label key={f.key} class="history-panel__filter-option">
                <input
                  type="checkbox"
                  checked={selectedFilters.has(f.key)}
                  onChange={() => toggleFilter(f.key)}
                />
                {f.label}
              </label>
            ))}
            {selectedFilters.size > 0 && (
              <button
                class="history-panel__filters-reset"
                onClick={() => setSelectedFilters(new Set())}
              >
                Show all changes
              </button>
            )}
          </div>
        </details>
      )}
      {filteredHistory.length === 0 ? (
        <div class="history-panel__empty">
          No changes match the current filters.{" "}
          <button
            class="history-panel__filters-reset"
            onClick={() => setSelectedFilters(new Set())}
          >
            Show all changes
          </button>
        </div>
      ) : (
        <div class="history-panel__list">
          {filteredHistory.map((event) => {
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
                <div class="history-panel__meta">
                  <span class="history-panel__user">
                    {event.user_display_name ?? "Unknown"}
                  </span>
                  <span class="history-panel__timestamp">
                    {formatTimestamp(event.timestamp)}
                  </span>
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
      )}
    </div>
  );
}
