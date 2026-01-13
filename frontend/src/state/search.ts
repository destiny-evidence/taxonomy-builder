import { signal } from "@preact/signals";

/** Current search query string */
export const searchQuery = signal("");

/** Whether to hide non-matching concepts (vs. grey them out) */
export const hideNonMatches = signal(false);

/**
 * Check if a concept matches the search query.
 * Matches against pref_label and alt_labels, case-insensitively.
 */
export function conceptMatchesSearch(
  prefLabel: string,
  altLabels: string[],
  query: string
): boolean {
  if (!query) return true;

  const lowerQuery = query.toLowerCase();

  if (prefLabel.toLowerCase().includes(lowerQuery)) {
    return true;
  }

  for (const altLabel of altLabels) {
    if (altLabel.toLowerCase().includes(lowerQuery)) {
      return true;
    }
  }

  return false;
}
