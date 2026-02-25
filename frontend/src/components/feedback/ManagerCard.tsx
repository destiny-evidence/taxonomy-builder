import { useSignal } from "@preact/signals";
import { route } from "preact-router";
import type { FeedbackManagerRead } from "../../types/models";
import { feedbackManagerApi } from "../../api/feedback";
import { conceptsApi } from "../../api/concepts";
import { allFeedback } from "../../state/feedback";
import { ApiError } from "../../api/client";
import { LoadingOverlay } from "../common/LoadingOverlay";
import "./ManagerCard.css";

interface ManagerCardProps {
  item: FeedbackManagerRead;
  projectId: string;
}

const STATUS_BADGE: Record<string, string> = {
  open: "manager-card__badge--warning",
  responded: "manager-card__badge--primary",
  resolved: "manager-card__badge--success",
  declined: "manager-card__badge--muted",
};

const ENTITY_BADGE: Record<string, string> = {
  concept: "manager-card__badge--concept",
  scheme: "manager-card__badge--scheme",
  class: "manager-card__badge--class",
  property: "manager-card__badge--property",
};

const DATE_FORMAT: Intl.DateTimeFormatOptions = {
  year: "numeric",
  month: "short",
  day: "numeric",
};

export function ManagerCard({ item, projectId }: ManagerCardProps) {
  const expanded = useSignal(false);
  const responseText = useSignal("");
  const loading = useSignal(false);
  const error = useSignal<string | null>(null);

  function updateItem(updated: FeedbackManagerRead) {
    allFeedback.value = allFeedback.value.map((fb) =>
      fb.id === updated.id ? updated : fb,
    );
  }

  async function handleAction(
    action: "respond" | "resolve" | "decline",
  ) {
    loading.value = true;
    error.value = null;
    try {
      let updated: FeedbackManagerRead;
      if (action === "respond") {
        updated = await feedbackManagerApi.respond(item.id, responseText.value);
      } else if (action === "resolve") {
        updated = await feedbackManagerApi.resolve(
          item.id,
          responseText.value || undefined,
        );
      } else {
        updated = await feedbackManagerApi.decline(
          item.id,
          responseText.value || undefined,
        );
      }
      updateItem(updated);
      responseText.value = "";
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        error.value = "This item has already been resolved or declined. Refresh to see the latest state.";
      } else {
        error.value = err instanceof Error ? err.message : "Action failed";
      }
    } finally {
      loading.value = false;
    }
  }

  async function handleViewInBuilder(e: Event) {
    e.preventDefault();
    e.stopPropagation();

    if (item.entity_type === "scheme") {
      route(`/projects/${projectId}/schemes/${item.entity_id}`);
    } else if (item.entity_type === "concept") {
      try {
        const concept = await conceptsApi.get(item.entity_id);
        route(`/projects/${projectId}/schemes/${concept.scheme_id}`);
      } catch {
        // Concept may have been deleted — fall back to project
        route(`/projects/${projectId}`);
      }
    } else {
      // Classes and properties — no URL route, go to project workspace
      route(`/projects/${projectId}`);
    }
  }

  const isTerminal =
    item.status === "resolved" || item.status === "declined";
  const excerpt =
    item.content.length > 120
      ? item.content.slice(0, 120) + "..."
      : item.content;
  const date = new Date(item.created_at).toLocaleDateString(undefined, DATE_FORMAT);

  return (
    <div
      class={`manager-card ${expanded.value ? "manager-card--expanded" : ""}`}
      style="position:relative"
      onClick={() => (expanded.value = !expanded.value)}
    >
      {loading.value && <LoadingOverlay />}

      <div class="manager-card__header">
        <span class="manager-card__entity-label">{item.entity_label}</span>
        <span
          class={`manager-card__badge ${ENTITY_BADGE[item.entity_type] ?? ""}`}
        >
          {formatEntityType(item.entity_type)}
        </span>
        <span class="manager-card__badge manager-card__badge--muted">
          {formatFeedbackType(item.feedback_type)}
        </span>
        <span
          class={`manager-card__badge ${STATUS_BADGE[item.status] ?? ""}`}
        >
          {item.status}
        </span>
        <span class="manager-card__meta">
          {item.author_name} &middot; {date}
        </span>
      </div>

      {!expanded.value && (
        <div class="manager-card__excerpt">{excerpt}</div>
      )}

      {expanded.value && (
        <div
          class="manager-card__detail"
          onClick={(e) => e.stopPropagation()}
        >
          <p class="manager-card__content">{item.content}</p>
          <div class="manager-card__version">
            Filed against <span class="manager-card__version-tag">v{item.snapshot_version}</span>
          </div>

          {item.response && (
            <div class="manager-card__response">
              <div class="manager-card__response-meta">
                Responded on{" "}
                {new Date(item.response.created_at).toLocaleDateString(undefined, DATE_FORMAT)}
                {item.responded_by_name && ` by ${item.responded_by_name}`}
              </div>
              <div class="manager-card__response-content">{item.response.content}</div>
            </div>
          )}

          {error.value && <div class="manager-card__error">{error.value}</div>}

          <div class="manager-card__actions">
            {!isTerminal && (
              <textarea
                class="manager-card__textarea"
                placeholder="Write a response..."
                value={responseText.value}
                onInput={(e) => {
                  responseText.value = (e.target as HTMLTextAreaElement).value;
                }}
              />
            )}
            <div class="manager-card__buttons">
              {!isTerminal && (
                <button
                  class="manager-card__btn manager-card__btn--primary"
                  disabled={!responseText.value.trim() || loading.value}
                  onClick={() => handleAction("respond")}
                >
                  Respond
                </button>
              )}
              {item.status !== "resolved" && (
                <button
                  class="manager-card__btn manager-card__btn--success"
                  disabled={loading.value}
                  onClick={() => handleAction("resolve")}
                >
                  Resolve
                </button>
              )}
              {item.status !== "declined" && (
                <button
                  class="manager-card__btn manager-card__btn--outline"
                  disabled={loading.value}
                  onClick={() => handleAction("decline")}
                >
                  Decline
                </button>
              )}
              <a
                href="#"
                class="manager-card__btn manager-card__btn--link"
                title={viewTooltip(item)}
                onClick={handleViewInBuilder}
              >
                View in builder
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function viewTooltip(item: FeedbackManagerRead): string {
  const base = `Feedback filed against v${item.snapshot_version}`;
  if (item.entity_type === "concept") return `Opens scheme for this concept. ${base}`;
  if (item.entity_type === "scheme") return `Opens this scheme. ${base}`;
  return `Opens project workspace. ${base}`;
}

function formatEntityType(type: string): string {
  if (type === "class") return "Class";
  return type.charAt(0).toUpperCase() + type.slice(1);
}

function formatFeedbackType(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
