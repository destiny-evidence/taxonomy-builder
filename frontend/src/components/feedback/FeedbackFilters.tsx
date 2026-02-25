import {
  statusFilter,
  entityTypeFilter,
  feedbackTypeFilter,
  searchQuery,
  filteredFeedback,
  availableFeedbackTypes,
} from "../../state/feedback";
import type { FeedbackStatus } from "../../types/models";
import "./FeedbackFilters.css";

const ENTITY_TYPES = [
  { value: "", label: "All types" },
  { value: "concept", label: "Concept" },
  { value: "scheme", label: "Scheme" },
  { value: "class", label: "Class" },
  { value: "property", label: "Property" },
];

const STATUS_OPTIONS: { value: FeedbackStatus | ""; label: string }[] = [
  { value: "", label: "All statuses" },
  { value: "open", label: "Open" },
  { value: "responded", label: "Responded" },
  { value: "resolved", label: "Resolved" },
  { value: "declined", label: "Declined" },
];

export function FeedbackFilters() {
  const fbTypes = availableFeedbackTypes.value;
  const count = filteredFeedback.value.length;

  return (
    <div class="feedback-filters">
      <input
        type="text"
        class="feedback-filters__search"
        placeholder="Search feedback..."
        value={searchQuery.value}
        onInput={(e) => {
          searchQuery.value = (e.target as HTMLInputElement).value;
        }}
      />
      <select
        class="feedback-filters__select"
        value={entityTypeFilter.value}
        onChange={(e) => {
          entityTypeFilter.value = (e.target as HTMLSelectElement).value;
        }}
      >
        {ENTITY_TYPES.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <select
        class="feedback-filters__select"
        value={feedbackTypeFilter.value}
        onChange={(e) => {
          feedbackTypeFilter.value = (e.target as HTMLSelectElement).value;
        }}
      >
        <option value="">All feedback types</option>
        {fbTypes.map((t) => (
          <option key={t} value={t}>
            {formatFeedbackType(t)}
          </option>
        ))}
      </select>
      <select
        class="feedback-filters__select"
        value={statusFilter.value}
        onChange={(e) => {
          statusFilter.value = (e.target as HTMLSelectElement)
            .value as FeedbackStatus | "";
        }}
      >
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <span class="feedback-filters__count">{count} items</span>
    </div>
  );
}

function formatFeedbackType(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
