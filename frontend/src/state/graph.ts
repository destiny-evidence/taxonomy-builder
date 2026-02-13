import { signal, computed } from "@preact/signals";
import { concepts } from "./concepts";
import type { GraphData, GraphNode, GraphEdge } from "../components/graph/graphTypes";

export type ViewMode = "tree" | "graph";

export const viewMode = signal<ViewMode>("tree");

export const graphData = computed<GraphData>(() => {
  const allConcepts = concepts.value;

  const nodes: GraphNode[] = allConcepts.map((c) => ({
    id: c.id,
    label: c.pref_label,
    definition: c.definition,
    isRoot: c.broader.length === 0,
  }));

  const edges: GraphEdge[] = [];

  // Broader edges: child -> parent
  for (const concept of allConcepts) {
    for (const parent of concept.broader) {
      edges.push({ source: concept.id, target: parent.id, type: "broader" });
    }
  }

  // Related edges: deduplicate symmetric pairs
  const seenRelated = new Set<string>();
  for (const concept of allConcepts) {
    for (const rel of concept.related) {
      const key = [concept.id, rel.id].sort().join(":");
      if (!seenRelated.has(key)) {
        seenRelated.add(key);
        edges.push({ source: concept.id, target: rel.id, type: "related" });
      }
    }
  }

  return { nodes, edges };
});
