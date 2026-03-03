import { signal } from "@preact/signals";
import { vocabulary } from "./vocabulary";

/** Set of node IDs (scheme IDs + concept IDs) that are expanded in the sidebar. */
export const expandedIds = signal<Set<string>>(new Set());

export function toggleExpanded(id: string) {
  const next = new Set(expandedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  expandedIds.value = next;
}

/** Expand the given IDs without collapsing anything. */
function expandAll(ids: string[]) {
  if (ids.length === 0) return;
  const next = new Set(expandedIds.value);
  for (const id of ids) next.add(id);
  expandedIds.value = next;
}

/**
 * Reveal an entity in the sidebar by expanding its scheme and all ancestor
 * concept nodes. For schemes, just expands the scheme. For classes/properties,
 * no tree expansion needed (they're flat lists under DataModelSection).
 */
export function revealEntity(entityKind: string, entityId: string) {
  if (entityKind === "scheme") {
    expandAll([entityId]);
    return;
  }
  if (entityKind === "class") {
    expandAll(["__classes__"]);
    return;
  }
  if (entityKind === "property") {
    expandAll(["__properties__"]);
    return;
  }
  if (entityKind !== "concept") return;

  const vocab = vocabulary.value;
  if (!vocab) return;

  for (const scheme of vocab.schemes) {
    const concept = scheme.concepts[entityId];
    if (!concept) continue;

    // Walk up broader relationships to collect all ancestors
    const toExpand = [scheme.id];
    const visited = new Set<string>();
    const queue = [...concept.broader];
    while (queue.length > 0) {
      const id = queue.pop()!;
      if (visited.has(id)) continue;
      visited.add(id);
      toExpand.push(id);
      const ancestor = scheme.concepts[id];
      if (ancestor) {
        for (const broaderId of ancestor.broader) {
          queue.push(broaderId);
        }
      }
    }
    expandAll(toExpand);
    return;
  }
}
