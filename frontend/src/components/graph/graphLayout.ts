import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide, forceX, forceY } from "d3-force";
import type { Simulation } from "d3-force";
import type { GraphNode, GraphEdge } from "./graphTypes";

export function createSimulation(
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number,
): Simulation<GraphNode, GraphEdge> {
  return forceSimulation<GraphNode>(nodes)
    .force(
      "link",
      forceLink<GraphNode, GraphEdge>(edges)
        .id((d) => d.id)
        .distance(80),
    )
    .force("charge", forceManyBody().strength(-200))
    .force("center", forceCenter(width / 2, height / 2))
    .force("x", forceX<GraphNode>(width / 2).strength(0.05))
    .force("y", forceY<GraphNode>(height / 2).strength(0.05))
    .force("collide", forceCollide<GraphNode>().radius(20));
}
