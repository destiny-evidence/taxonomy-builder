import { useSignal } from "@preact/signals";
import { isAuthenticated } from "../../state/auth";
import { currentEntityFeedback } from "../../state/feedback";
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
  const filter = useSignal<StatusFilter>("all");

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
  const filtered =
    filter.value === "all"
      ? allFeedback
      : allFeedback.filter((fb) =>
          filter.value === "open"
            ? fb.status === "open"
            : fb.status === "resolved" || fb.status === "declined"
        );

  const filters: { key: StatusFilter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "open", label: "Open" },
    { key: "resolved", label: "Resolved" },
  ];

  return (
    <div class="feedback-section">
      <div class="feedback-section__header">
        <span class="feedback-section__title">Your Feedback</span>
        {allFeedback.length > 0 && (
          <span class="feedback-section__count">{allFeedback.length}</span>
        )}
      </div>

      {allFeedback.length > 0 && (
        <div class="feedback-section__filters">
          {filters.map((f) => (
            <button
              key={f.key}
              class={`feedback-section__filter-btn${
                filter.value === f.key
                  ? " feedback-section__filter-btn--active"
                  : ""
              }`}
              onClick={() => (filter.value = f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}

      {filtered.length > 0 ? (
        filtered.map((fb) => <FeedbackCard key={fb.id} feedback={fb} />)
      ) : allFeedback.length > 0 ? (
        <div class="feedback-section__empty">
          No {filter.value} feedback
        </div>
      ) : (
        <div class="feedback-section__empty">
          No feedback yet on this entity
        </div>
      )}

      <FeedbackForm
        entityType={entityType}
        entityId={entityId}
        entityLabel={entityLabel}
      />
    </div>
  );
}
