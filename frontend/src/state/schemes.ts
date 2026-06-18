import { signal } from "@preact/signals";
import type { ConceptScheme } from "../types/models";

export const schemes = signal<ConceptScheme[]>([]);
export const schemesLoading = signal(false);
export const schemesError = signal<string | null>(null);
export const currentScheme = signal<ConceptScheme | null>(null);

/**
 * Compute the result of moving a scheme within its project's display order.
 *
 * Returns the full scheme list with the project's schemes reordered and their
 * `position` fields renumbered as a gapless 0..n-1 sequence, plus the moved
 * item's new index. Schemes belonging to other projects are left in place.
 * Returns null when the move is a no-op (dropped on itself or unknown ids).
 */
export function reorderSchemes(
  all: ConceptScheme[],
  projectId: string,
  activeId: string,
  overId: string,
): { schemes: ConceptScheme[]; newIndex: number } | null {
  const projectItems = all.filter((s) => s.project_id === projectId);
  const oldIndex = projectItems.findIndex((s) => s.id === activeId);
  const newIndex = projectItems.findIndex((s) => s.id === overId);
  if (oldIndex === -1 || newIndex === -1 || oldIndex === newIndex) {
    return null;
  }

  const reordered = [...projectItems];
  const [moved] = reordered.splice(oldIndex, 1);
  reordered.splice(newIndex, 0, moved);
  const withPosition = reordered.map((s, i) => ({ ...s, position: i }));

  // Slot the renumbered project items back into their original positions in the
  // full list, preserving the order of any other projects' schemes.
  let next = 0;
  const merged = all.map((s) =>
    s.project_id === projectId ? withPosition[next++] : s,
  );

  return { schemes: merged, newIndex };
}
