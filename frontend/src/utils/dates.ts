/**
 * Format an ISO date string as a human-readable date with time.
 * e.g. "Jan 1, 2024, 12:00 AM"
 */
export function formatDatetime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format an ISO date string as a human-readable date without time.
 * e.g. "Jan 1, 2024"
 */
export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
