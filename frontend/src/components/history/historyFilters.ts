export interface HistoryFilter {
  key: string;
  label: string;
  types: string[];
}

export const HISTORY_FILTERS: HistoryFilter[] = [
  { key: "concepts", label: "Concepts", types: ["concept"] },
  { key: "schemes", label: "Schemes", types: ["concept_scheme"] },
  { key: "properties", label: "Properties", types: ["property"] },
  { key: "relationships", label: "Relationships", types: ["concept_broader", "concept_related"] },
  { key: "project", label: "Project settings", types: ["project"] },
];

/** Filter keys relevant to each history source type. */
export const SOURCE_FILTERS: Record<string, string[]> = {
  scheme: ["concepts", "schemes", "relationships", "properties", "project"],
  project: ["properties", "project"],
};

/**
 * Convert selected filter keys to a set of allowed entity types.
 * Returns null when no filters selected (meaning show all).
 */
export function getAllowedEntityTypes(selected: Set<string>): Set<string> | null {
  if (selected.size === 0) return null;
  const allowed = new Set<string>();
  for (const f of HISTORY_FILTERS) {
    if (selected.has(f.key)) f.types.forEach((t) => allowed.add(t));
  }
  return allowed;
}
