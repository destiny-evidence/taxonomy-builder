import { useEffect, useMemo, useState } from "preact/hooks";
import type { JSX } from "preact";
import { getSchemeHistory, getProjectHistory } from "../../api/history";
import { getActionLabel, getEntityTypeLabel } from "./historyStrings";
import { HISTORY_FILTERS, SOURCE_FILTERS, getAllowedEntityTypes } from "./historyFilters";
import type { ChangeEvent } from "../../types/models";
import "./HistoryPanel.css";

export type HistorySource =
  | { type: "scheme"; id: string }
  | { type: "project"; id: string };

interface HistoryPanelProps {
  source: HistorySource;
  refreshKey?: number;
}

/** Entity types that display a single bold label from state. */
const LABEL_FIELDS: Record<string, { field: string; prefix?: string }> = {
  concept: { field: "pref_label" },
  property: { field: "label" },
  project: { field: "name" },
  concept_scheme: { field: "title" },
  published_version: { field: "version_label", prefix: "v" },
};

/** Relationship entity types that display "left {arrow} right". */
const RELATIONSHIP_FIELDS: Record<string, { left: string; right: string; arrow: string }> = {
  concept_broader: { left: "concept_label", right: "broader_label", arrow: " → " },
  concept_related: { left: "concept_label", right: "related_label", arrow: " ↔ " },
};

/**
 * Render a human-readable description of what changed.
 */
function ChangeDescription({ event }: { event: ChangeEvent }): JSX.Element | null {
  const afterState = event.after_state as Record<string, unknown> | null;
  const beforeState = event.before_state as Record<string, unknown> | null;

  const rel = RELATIONSHIP_FIELDS[event.entity_type];
  if (rel) {
    const left = afterState?.[rel.left] || beforeState?.[rel.left];
    const right = afterState?.[rel.right] || beforeState?.[rel.right];
    if (left && right) {
      return (
        <>
          <strong>{left as string}</strong>
          {rel.arrow}
          <strong>{right as string}</strong>
        </>
      );
    }
    return null;
  }

  const desc = LABEL_FIELDS[event.entity_type];
  if (desc) {
    const value = afterState?.[desc.field] || beforeState?.[desc.field];
    if (value && typeof value === "string") {
      return <strong>{desc.prefix ?? ""}{value}</strong>;
    }
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
  const defaultFilters = useMemo(() => {
    if (source.type === "project") {
      return new Set(["properties"]);
    }
    // Scheme view: focus on concepts by default
    return new Set(["concepts"]);
  }, [source.type]);
  const [selectedFilters, setSelectedFilters] = useState<Set<string>>(defaultFilters);

  // Reset filters when navigating to a different source
  useEffect(() => {
    setSelectedFilters(defaultFilters);
  }, [source.type, source.id]);

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

  const allowedKeys = SOURCE_FILTERS[source.type] ?? HISTORY_FILTERS.map((f) => f.key);
  const relevantFilters = useMemo(
    () => HISTORY_FILTERS.filter((f) => allowedKeys.includes(f.key) && history.some((e) => f.types.includes(e.entity_type))),
    [history, allowedKeys],
  );

  // If the default filter has no matches, activate all relevant filters
  useEffect(() => {
    if (history.length === 0) return;
    const allowed = getAllowedEntityTypes(selectedFilters);
    if (allowed && !history.some((e) => allowed.has(e.entity_type))) {
      setSelectedFilters(new Set(relevantFilters.map((f) => f.key)));
    }
  }, [history, relevantFilters]);

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

  return (
    <div class="history-panel">
      <div class="history-panel__filters">
        <span class="history-panel__filters-label">Show only</span>
        <div class="history-panel__filters-pills">
          {relevantFilters.map((f) => (
            <button
              key={f.key}
              class={`history-panel__filter-pill${selectedFilters.has(f.key) ? " history-panel__filter-pill--active" : ""}`}
              onClick={() => toggleFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>
      {filteredHistory.length === 0 ? (
        <div class="history-panel__empty">
          No changes match the current filters.
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
