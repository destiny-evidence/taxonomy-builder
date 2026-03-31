import { computed, signal } from "@preact/signals";
import { vocabulary, conceptTrees, type ConceptTreeNode } from "./vocabulary";
import { ownFeedback } from "./feedback";
import { expandedIds, revealEntity } from "./sidebar";
import { route } from "../router";

export const searchQuery = signal("");

/** Snapshot of expanded state before search began, so we can restore on clear. */
let preSearchExpandedIds: Set<string> | null = null;

/**
 * Clear the search query and restore the sidebar to its pre-search expanded state.
 */
export function clearSearch(): void {
  searchQuery.value = "";
  if (preSearchExpandedIds !== null) {
    expandedIds.value = preSearchExpandedIds;
    preSearchExpandedIds = null;
  }
  // Ensure the currently selected entity remains visible in the tree.
  const { entityKind, entityId } = route.value;
  if (entityKind && entityId) {
    revealEntity(entityKind, entityId);
  }
}

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
  const q = query.toLowerCase();
  if (prefLabel.toLowerCase().includes(q)) return true;
  for (const alt of altLabels) {
    if (alt.toLowerCase().includes(q)) return true;
  }
  return false;
}

/**
 * Expand all scheme and ancestor concept IDs that lead to matching concepts.
 */
export function expandMatchingPaths(query: string): void {
  const q = query.trim().toLowerCase();
  if (!q) return;

  const vocab = vocabulary.value;
  if (!vocab) return;

  // Snapshot the pre-search state on first search, restore it on subsequent
  // searches so we don't accumulate expansions across queries.
  if (preSearchExpandedIds === null) {
    preSearchExpandedIds = expandedIds.value;
  }
  const baseline = preSearchExpandedIds;

  const idsToExpand: string[] = [];

  for (const scheme of vocab.schemes) {
    let schemeHasMatch = false;

    for (const [, concept] of Object.entries(scheme.concepts)) {
      if (conceptMatchesSearch(concept.pref_label, concept.alt_labels, q)) {
        schemeHasMatch = true;
        // Walk up broader relationships to expand ancestors
        const visited = new Set<string>();
        const queue = [...concept.broader];
        while (queue.length > 0) {
          const ancestorId = queue.pop()!;
          if (visited.has(ancestorId)) continue;
          visited.add(ancestorId);
          idsToExpand.push(ancestorId);
          const ancestor = scheme.concepts[ancestorId];
          if (ancestor) {
            for (const broaderId of ancestor.broader) {
              queue.push(broaderId);
            }
          }
        }
      }
    }

    if (schemeHasMatch) {
      idsToExpand.push(scheme.id);
    }
  }

  const next = new Set(baseline);
  for (const id of idsToExpand) next.add(id);
  expandedIds.value = next;
}

export interface SearchResult {
  type: "concept" | "scheme" | "class" | "property" | "feedback";
  id: string;
  label: string;
  /** For feedback results, the entity this feedback is about. */
  entityId?: string;
  entityType?: string;
  snippet?: string;
}

export const searchResults = computed<SearchResult[]>(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return [];

  const vocab = vocabulary.value;
  if (!vocab) return [];

  const results: SearchResult[] = [];

  // Search schemes
  for (const scheme of vocab.schemes) {
    if (scheme.title.toLowerCase().includes(q)) {
      results.push({ type: "scheme", id: scheme.id, label: scheme.title });
    }

    // Search concepts
    for (const [id, concept] of Object.entries(scheme.concepts)) {
      const matchLabel = concept.pref_label.toLowerCase().includes(q);
      const matchAlt = concept.alt_labels.some((a) =>
        a.toLowerCase().includes(q)
      );
      if (matchLabel || matchAlt) {
        results.push({ type: "concept", id, label: concept.pref_label });
      }
    }
  }

  // Search classes
  for (const cls of vocab.classes) {
    if (cls.label.toLowerCase().includes(q)) {
      results.push({ type: "class", id: cls.id, label: cls.label });
    }
  }

  // Search properties
  for (const prop of vocab.properties) {
    if (prop.label.toLowerCase().includes(q)) {
      results.push({ type: "property", id: prop.id, label: prop.label });
    }
  }

  // Search own feedback content
  for (const fb of ownFeedback.value) {
    if (fb.content.toLowerCase().includes(q)) {
      results.push({
        type: "feedback",
        id: fb.id,
        label: fb.entity_label,
        entityId: fb.entity_id,
        entityType: fb.entity_type,
        snippet: fb.content.slice(0, 100),
      });
    }
  }

  return results;
});

/**
 * Concept trees annotated with match status for search-aware rendering.
 * When no search is active, returns trees with matchStatus "none" on all nodes.
 */
export const searchFilteredConceptTrees = computed<Map<string, ConceptTreeNode[]>>(() => {
  const trees = conceptTrees.value;
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return trees;

  const vocab = vocabulary.value;
  if (!vocab) return trees;

  const result = new Map<string, ConceptTreeNode[]>();
  const schemeConceptsMap = new Map<string, Record<string, import("../api/published").VocabConcept>>();
  for (const scheme of vocab.schemes) {
    schemeConceptsMap.set(scheme.id, scheme.concepts);
  }

  for (const [schemeId, nodes] of trees) {
    const concepts = schemeConceptsMap.get(schemeId) ?? {};
    result.set(schemeId, annotateNodes(nodes, q, concepts));
  }

  return result;
});

function annotateNodes(
  nodes: ConceptTreeNode[],
  query: string,
  concepts: Record<string, import("../api/published").VocabConcept>
): ConceptTreeNode[] {
  return nodes.map((node) => annotateNode(node, query, concepts));
}

function annotateNode(
  node: ConceptTreeNode,
  query: string,
  concepts: Record<string, import("../api/published").VocabConcept>
): ConceptTreeNode {
  const children = annotateNodes(node.children, query, concepts);
  const concept = concepts[node.id];
  const isMatch = concept
    ? conceptMatchesSearch(concept.pref_label, concept.alt_labels, query)
    : node.label.toLowerCase().includes(query);
  const childrenHaveMatch = children.some((c) => c.matchStatus !== "none");

  let matchStatus: ConceptTreeNode["matchStatus"] = "none";
  if (isMatch) {
    matchStatus = "match";
  } else if (childrenHaveMatch) {
    matchStatus = "ancestor";
  }

  return { ...node, children, matchStatus };
}
