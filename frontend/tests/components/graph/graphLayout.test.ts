import { describe, it, expect } from "vitest";
import { createSimulation } from "../../../src/components/graph/graphLayout";
import type { GraphNode, GraphEdge } from "../../../src/components/graph/graphTypes";

function makeNodes(count: number): GraphNode[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `n${i}`,
    label: `Node ${i}`,
    definition: null,
    isRoot: i === 0,
  }));
}

describe("createSimulation", () => {
  it("returns a d3 simulation", () => {
    const nodes: GraphNode[] = makeNodes(3);
    const edges: GraphEdge[] = [{ source: "n1", target: "n0", type: "broader" }];

    const sim = createSimulation(nodes, edges, 800, 600);
    expect(sim).toBeDefined();
    expect(typeof sim.tick).toBe("function");
    expect(typeof sim.stop).toBe("function");
    expect(typeof sim.nodes).toBe("function");
    sim.stop();
  });

  it("sets nodes on the simulation", () => {
    const nodes = makeNodes(3);
    const edges: GraphEdge[] = [];

    const sim = createSimulation(nodes, edges, 800, 600);
    expect(sim.nodes()).toHaveLength(3);
    sim.stop();
  });

  it("initializes node positions after ticking", () => {
    const nodes = makeNodes(2);
    const edges: GraphEdge[] = [];

    const sim = createSimulation(nodes, edges, 800, 600);
    sim.tick(1);

    for (const node of nodes) {
      expect(node.x).toBeDefined();
      expect(node.y).toBeDefined();
      expect(typeof node.x).toBe("number");
      expect(typeof node.y).toBe("number");
    }
    sim.stop();
  });

  it("handles empty graph", () => {
    const sim = createSimulation([], [], 800, 600);
    expect(sim.nodes()).toHaveLength(0);
    sim.stop();
  });
});
