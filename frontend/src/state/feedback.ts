import { signal, computed } from "@preact/signals";
import type { FeedbackManagerRead, FeedbackStatus } from "../types/models";

export const allFeedback = signal<FeedbackManagerRead[]>([]);
export const feedbackLoading = signal(false);
export const feedbackError = signal<string | null>(null);

// Filter state
export const statusFilter = signal<FeedbackStatus | "">("");
export const entityTypeFilter = signal("");
export const feedbackTypeFilter = signal("");
export const searchQuery = signal("");

export const filteredFeedback = computed(() => {
  let items = allFeedback.value;

  if (statusFilter.value) {
    items = items.filter((fb) => fb.status === statusFilter.value);
  }
  if (entityTypeFilter.value) {
    items = items.filter((fb) => fb.entity_type === entityTypeFilter.value);
  }
  if (feedbackTypeFilter.value) {
    items = items.filter((fb) => fb.feedback_type === feedbackTypeFilter.value);
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    items = items.filter(
      (fb) =>
        fb.content.toLowerCase().includes(q) ||
        fb.entity_label.toLowerCase().includes(q) ||
        fb.author_name.toLowerCase().includes(q) ||
        (fb.response?.content.toLowerCase().includes(q) ?? false),
    );
  }

  return items;
});

export const summaryStats = computed(() => {
  const items = allFeedback.value;
  return {
    total: items.length,
    open: items.filter((fb) => fb.status === "open").length,
    responded: items.filter((fb) => fb.status === "responded").length,
    resolved: items.filter((fb) => fb.status === "resolved").length,
    declined: items.filter((fb) => fb.status === "declined").length,
  };
});

// Unique feedback types for filter dropdown
export const availableFeedbackTypes = computed(() => {
  const types = new Set(allFeedback.value.map((fb) => fb.feedback_type));
  return [...types].sort();
});

export function resetFilters() {
  statusFilter.value = "";
  entityTypeFilter.value = "";
  feedbackTypeFilter.value = "";
  searchQuery.value = "";
}
