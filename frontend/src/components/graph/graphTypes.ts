import type { SimulationNodeDatum } from "d3-force";

export interface GraphNode extends SimulationNodeDatum {
  id: string;
  label: string;
  definition: string | null;
  isRoot: boolean;
}

export type EdgeType = "broader" | "related";

export interface GraphEdge {
  source: string;
  target: string;
  type: EdgeType;
}

/** Edge after D3 simulation replaces string IDs with node object references. */
export interface SimulatedEdge {
  source: GraphNode;
  target: GraphNode;
  type: EdgeType;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
