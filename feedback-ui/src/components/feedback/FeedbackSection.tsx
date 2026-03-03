import { useSignal } from "@preact/signals";
import { isAuthenticated } from "../../state/auth";
import { currentEntityFeedback } from "../../state/feedback";
import { selectedVersion } from "../../state/vocabulary";
import { login } from "../../api/auth";
import { FeedbackCard } from "./FeedbackCard";
import { FeedbackForm } from "./FeedbackForm";
import "./FeedbackSection.css";

type StatusFilter = "all" | "open" | "resolved";

interface FeedbackSectionProps {
  entityType: string;
  entityId: string;
  entityLabel: string;
}

export function FeedbackSection({
  entityType,
  entityId,
  entityLabel,
}: FeedbackSectionProps) {
  const statusFilter = useSignal<StatusFilter>("all");
  const versionOnly = useSignal(false);

  if (!isAuthenticated.value) {
    return (
      <div class="feedback-section">
        <div class="feedback-section__sign-in">
          <span
            class="feedback-section__sign-in-link"
            onClick={login}
          >
            Sign in
          </span>{" "}
          to provide feedback
        </div>
      </div>
    );
  }

  const allFeedback = currentEntityFeedback.value;
  const version = selectedVersion.value;

  let filtered = allFeedback;
  if (versionOnly.value && version) {
    filtered = filtered.filter((fb) => fb.snapshot_version === version);
  }
  if (statusFilter.value !== "all") {
    filtered = filtered.filter((fb) =>
      statusFilter.value === "open"
        ? fb.status === "open"
        : fb.status === "resolved" || fb.status === "declined"
    );
  }

  const statusFilters: { key: StatusFilter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "open", label: "Open" },
    { key: "resolved", label: "Resolved" },
  ];

  return (
    <div class="feedback-section">
      <div class="feedback-section__header">
        <span class="feedback-section__title">Submit Feedback</span>
      </div>

      <FeedbackForm
        entityType={entityType}
        entityId={entityId}
        entityLabel={entityLabel}
      />

      <div class="feedback-section__divider" />

      <div class="feedback-section__header">
        <span class="feedback-section__title">Your Feedback</span>
        {allFeedback.length > 0 && (
          <span class="feedback-section__count">{allFeedback.length}</span>
        )}
      </div>

      {allFeedback.length > 0 && (
        <div class="feedback-section__filters">
          {statusFilters.map((f) => (
            <button
              key={f.key}
              class={`feedback-section__filter-btn${
                statusFilter.value === f.key
                  ? " feedback-section__filter-btn--active"
                  : ""
              }`}
              aria-pressed={statusFilter.value === f.key}
              onClick={() => (statusFilter.value = f.key)}
            >
              {f.label}
            </button>
          ))}
          <span class="feedback-section__filter-divider" />
          <button
            class={`feedback-section__filter-btn${
              versionOnly.value ? " feedback-section__filter-btn--active" : ""
            }`}
            aria-pressed={versionOnly.value}
            onClick={() => (versionOnly.value = !versionOnly.value)}
          >
            This version only
          </button>
        </div>
      )}

      {filtered.length > 0 ? (
        filtered.map((fb) => <FeedbackCard key={fb.id} feedback={fb} />)
      ) : allFeedback.length > 0 ? (
        <div class="feedback-section__empty">
          No matching feedback
        </div>
      ) : (
        <div class="feedback-section__empty">
          No feedback submitted yet for this entity.
        </div>
      )}
    </div>
  );
}
