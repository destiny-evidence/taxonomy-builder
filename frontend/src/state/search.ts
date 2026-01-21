import { signal } from "@preact/signals";
import type { TreeNode } from "../types/models";
import { treeData, expandedPaths } from "./concepts";

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

/**
 * Expand all paths that lead to matching concepts.
 * Preserves any already-expanded paths.
 */
export function expandMatchingPaths(query: string): void {
  if (!query) return;

  const pathsToExpand: string[] = [];

  function findMatchingPaths(
    nodes: TreeNode[],
    parentPath: string = ""
  ): boolean {
    let hasMatch = false;

    for (const node of nodes) {
      const path = parentPath ? `${parentPath}/${node.id}` : node.id;
      const isMatch = conceptMatchesSearch(node.pref_label, node.alt_labels, query);
      const childrenHaveMatch = findMatchingPaths(node.narrower, path);

      if (isMatch || childrenHaveMatch) {
        hasMatch = true;
        // Add parent path (not the matching node itself) to expand
        if (parentPath && (isMatch || childrenHaveMatch)) {
          pathsToExpand.push(parentPath);
        }
      }
    }

    return hasMatch;
  }

  findMatchingPaths(treeData.value);

  if (pathsToExpand.length > 0) {
    const newExpanded = new Set(expandedPaths.value);
    for (const path of pathsToExpand) {
      newExpanded.add(path);
    }
    expandedPaths.value = newExpanded;
  }
}
