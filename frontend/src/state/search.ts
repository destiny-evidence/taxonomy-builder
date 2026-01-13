import { signal } from "@preact/signals";

/** Current search query string */
export const searchQuery = signal("");

/** Whether to hide non-matching concepts (vs. grey them out) */
export const hideNonMatches = signal(false);
