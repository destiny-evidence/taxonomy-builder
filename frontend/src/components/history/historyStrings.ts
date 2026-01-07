/**
 * Human-readable labels for history event display.
 */

export const ACTION_LABELS: Record<string, string> = {
  create: "Created",
  update: "Updated",
  delete: "Deleted",
  publish: "Published",
};

export const ENTITY_TYPE_LABELS: Record<string, string> = {
  concept: "Concept",
  concept_scheme: "Scheme",
  concept_broader: "Broader relationship",
  concept_related: "Related relationship",
  published_version: "Version",
};

/**
 * Get human-readable action label.
 */
export function getActionLabel(action: string): string {
  return ACTION_LABELS[action] || action;
}

/**
 * Get human-readable entity type label.
 */
export function getEntityTypeLabel(entityType: string): string {
  return ENTITY_TYPE_LABELS[entityType] || entityType;
}
