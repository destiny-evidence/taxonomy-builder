import { signal, computed } from "@preact/signals";
import type { Concept, TreeNode, RenderNode } from "../types/models";

export const concepts = signal<Concept[]>([]);

export const treeData = signal<TreeNode[]>([]);
export const treeLoading = signal(false);

export const selectedConceptId = signal<string | null>(null);
export const expandedPaths = signal<Set<string>>(new Set());

export const conceptsById = computed(() => {
  const map = new Map<string, Concept>();
  for (const concept of concepts.value) {
    map.set(concept.id, concept);
  }
  return map;
});

export const selectedConcept = computed(() => {
  const id = selectedConceptId.value;
  return id ? conceptsById.value.get(id) ?? null : null;
});

// Build render tree with multi-parent detection
export const renderTree = computed(() => {
  const idOccurrences = new Map<string, string[]>(); // id -> all parent labels

  // First pass: count occurrences and track parent labels
  function countOccurrences(
    nodes: TreeNode[],
    parentLabel: string | null = null
  ) {
    for (const node of nodes) {
      const labels = idOccurrences.get(node.id) || [];
      if (parentLabel) {
        labels.push(parentLabel);
      }
      idOccurrences.set(node.id, labels);
      countOccurrences(node.narrower, node.pref_label);
    }
  }
  countOccurrences(treeData.value);

  // Second pass: build render nodes
  function buildNodes(
    nodes: TreeNode[],
    parentPath: string = "",
    depth: number = 0,
    currentParentLabel: string | null = null
  ): RenderNode[] {
    return nodes.map((node) => {
      const path = parentPath ? `${parentPath}/${node.id}` : node.id;
      const allParentLabels = idOccurrences.get(node.id) || [];
      const hasMultipleParents = allParentLabels.length > 1;

      // Get other parent labels (excluding current)
      const otherParentLabels = currentParentLabel
        ? allParentLabels.filter((l) => l !== currentParentLabel)
        : allParentLabels.slice(1);

      return {
        id: node.id,
        pref_label: node.pref_label,
        definition: node.definition,
        path,
        depth,
        hasMultipleParents,
        otherParentLabels,
        children: buildNodes(node.narrower, path, depth + 1, node.pref_label),
      };
    });
  }

  return buildNodes(treeData.value);
});

// ============ Drag and Drop State ============

export const isDragging = signal(false);
export const draggedConceptId = signal<string | null>(null);
export const draggedPath = signal<string | null>(null);
export const dropTargetId = signal<string | null>(null);
export const isAltKeyPressed = signal(false);

// Helper to extract parent ID from path
export function getParentIdFromPath(path: string): string | null {
  const parts = path.split("/");
  if (parts.length <= 1) return null;
  return parts[parts.length - 2];
}

// Computed: get all descendant IDs of dragged concept (for invalid drop detection)
export const draggedDescendantIds = computed(() => {
  const draggedId = draggedConceptId.value;
  if (!draggedId) return new Set<string>();

  const descendants = new Set<string>();

  function collectDescendants(nodes: RenderNode[]): boolean {
    for (const node of nodes) {
      if (node.id === draggedId) {
        // Found the dragged node, collect all its descendants
        collectAllChildren(node.children);
        return true;
      }
      if (collectDescendants(node.children)) {
        return true;
      }
    }
    return false;
  }

  function collectAllChildren(nodes: RenderNode[]) {
    for (const node of nodes) {
      descendants.add(node.id);
      collectAllChildren(node.children);
    }
  }

  collectDescendants(renderTree.value);
  return descendants;
});

// Check if drop target is valid
export function isValidDropTarget(
  targetId: string,
  draggedId: string,
  currentParentId: string | null
): boolean {
  // Cannot drop on self
  if (targetId === draggedId) return false;

  // Cannot drop on current parent (no-op)
  if (targetId === currentParentId) return false;

  // Cannot drop on descendant
  if (draggedDescendantIds.value.has(targetId)) return false;

  return true;
}
