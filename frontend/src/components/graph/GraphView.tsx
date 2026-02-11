import { useRef, useEffect, useMemo } from "preact/hooks";
import { select } from "d3-selection";
import { zoom as d3Zoom } from "d3-zoom";
import { drag as d3Drag } from "d3-drag";
import type { D3DragEvent } from "d3-drag";
import type { ZoomBehavior } from "d3-zoom";
import { forceCenter } from "d3-force";
import type { Simulation } from "d3-force";
import { graphData } from "../../state/graph";
import { selectedConceptId } from "../../state/concepts";
import { searchQuery, conceptMatchesSearch } from "../../state/search";
import { concepts } from "../../state/concepts";
import { createSimulation } from "./graphLayout";
import type { GraphNode, GraphEdge, SimulatedEdge } from "./graphTypes";
import "./GraphView.css";

const NODE_RADIUS = 6;
const ROOT_RADIUS = 8;
const LABEL_OFFSET = 14;

export function GraphView() {
  const svgRef = useRef<SVGSVGElement>(null);
  const simRef = useRef<Simulation<GraphNode, GraphEdge> | null>(null);
  const nodeSelRef = useRef<ReturnType<typeof select<SVGGElement, GraphNode>> | null>(null);
  const edgeSelRef = useRef<ReturnType<typeof select<SVGLineElement, GraphEdge>> | null>(null);

  const { nodes, edges } = graphData.value;
  const selected = selectedConceptId.value;
  const query = searchQuery.value;

  // Build set of matching concept IDs for search dimming
  const matchingIds = query
    ? new Set(
        concepts.value
          .filter((c) => conceptMatchesSearch(c.pref_label, c.alt_labels, query))
          .map((c) => c.id),
      )
    : null;

  // Build neighbor map for hover highlighting
  const neighbors = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const edge of edges) {
      if (!map.has(edge.source)) map.set(edge.source, new Set());
      if (!map.has(edge.target)) map.set(edge.target, new Set());
      map.get(edge.source)!.add(edge.target);
      map.get(edge.target)!.add(edge.source);
    }
    return map;
  }, [edges]);

  // Structural effect: build simulation, SVG elements, zoom, drag.
  // Only reruns when the graph data actually changes.
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg || nodes.length === 0) return;

    const width = svg.clientWidth || 800;
    const height = svg.clientHeight || 600;

    // Clear previous content
    const svgSel = select(svg);
    svgSel.selectAll("*").remove();

    // Arrow marker for broader edges
    svgSel
      .append("defs")
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -4 8 8")
      .attr("refX", 16)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4Z")
      .attr("class", "graph-view__arrow");

    // Zoom container
    const g = svgSel.append("g");

    const zoomBehavior: ZoomBehavior<SVGSVGElement, unknown> = d3Zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svgSel.call(zoomBehavior);

    // Deep-copy nodes/edges for D3 mutation
    const simNodes: GraphNode[] = nodes.map((n) => ({ ...n }));
    const simEdges: GraphEdge[] = edges.map((e) => ({ ...e }));

    // Create simulation
    const sim = createSimulation(simNodes, simEdges, width, height);
    simRef.current = sim;

    // Draw edges
    const edgeSelection = g
      .append("g")
      .attr("class", "graph-view__edges")
      .selectAll("line")
      .data(simEdges)
      .enter()
      .append("line")
      .attr("class", (d: GraphEdge) => `graph-view__edge graph-view__edge--${d.type}`)
      .attr("marker-end", (d: GraphEdge) => (d.type === "broader" ? "url(#arrowhead)" : null));

    // Draw nodes
    const nodeSelection = g
      .append("g")
      .attr("class", "graph-view__nodes")
      .selectAll("g")
      .data(simNodes)
      .enter()
      .append("g")
      .attr("class", (d: GraphNode) => {
        const classes = ["graph-view__node"];
        if (d.isRoot) classes.push("graph-view__node--root");
        return classes.join(" ");
      });

    nodeSelection
      .append("circle")
      .attr("r", (d: GraphNode) => (d.isRoot ? ROOT_RADIUS : NODE_RADIUS));

    nodeSelection
      .append("text")
      .attr("dy", LABEL_OFFSET)
      .text((d: GraphNode) => d.label);

    // Click -> select concept
    nodeSelection.on("click", (_event: MouseEvent, d: GraphNode) => {
      selectedConceptId.value = d.id;
    });

    // Hover -> highlight neighbors
    nodeSelection
      .on("mouseenter", (_event: MouseEvent, d: GraphNode) => {
        const neighborSet = neighbors.get(d.id) || new Set();
        svgSel.classed("graph-view--hovering", true);
        nodeSelection.classed("graph-view__node--dimmed", (n: GraphNode) => n.id !== d.id && !neighborSet.has(n.id));
        edgeSelection.classed("graph-view__edge--dimmed", (e) => {
          // D3 simulation replaces string source/target with node objects
          const { source, target } = e as unknown as SimulatedEdge;
          return source.id !== d.id && target.id !== d.id;
        });
      })
      .on("mouseleave", () => {
        svgSel.classed("graph-view--hovering", false);
        nodeSelection.classed("graph-view__node--dimmed", false);
        edgeSelection.classed("graph-view__edge--dimmed", false);
      });

    // Drag behavior
    const dragBehavior = d3Drag<SVGGElement, GraphNode>()
      .on("start", (event: D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) => {
        if (!event.active) sim.alpha(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event: D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event: D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) => {
        if (!event.active) sim.alpha(0);
        d.fx = null;
        d.fy = null;
      });

    // d3-drag's generic doesn't align with d3-selection's here; cast is standard practice
    nodeSelection.call(dragBehavior as any);

    // Tick: update positions (D3 has mutated edge source/target to node refs)
    sim.on("tick", () => {
      edgeSelection
        .attr("x1", (d) => (d as unknown as SimulatedEdge).source.x!)
        .attr("y1", (d) => (d as unknown as SimulatedEdge).source.y!)
        .attr("x2", (d) => (d as unknown as SimulatedEdge).target.x!)
        .attr("y2", (d) => (d as unknown as SimulatedEdge).target.y!);

      nodeSelection.attr("transform", (d: GraphNode) => `translate(${d.x},${d.y})`);
    });

    // Handle resize
    const svgEl = svg; // capture narrowed type for closure
    function handleResize() {
      const newWidth = svgEl.clientWidth || 800;
      const newHeight = svgEl.clientHeight || 600;
      sim.force("center", forceCenter(newWidth / 2, newHeight / 2));
      sim.alpha(0.1).restart();
    }

    window.addEventListener("resize", handleResize);

    // Store selections for the highlight effect
    nodeSelRef.current = nodeSelection as any;
    edgeSelRef.current = edgeSelection as any;

    return () => {
      sim.stop();
      simRef.current = null;
      nodeSelRef.current = null;
      edgeSelRef.current = null;
      window.removeEventListener("resize", handleResize);
    };
  }, [nodes, edges]);

  // Visual-only effect: update selection and search highlight classes
  // without rebuilding the simulation or resetting zoom/layout.
  useEffect(() => {
    const nodeSelection = nodeSelRef.current;
    if (!nodeSelection) return;

    nodeSelection.classed("graph-view__node--selected", (d: GraphNode) => d.id === selected);
    nodeSelection.classed(
      "graph-view__node--search-dimmed",
      (d: GraphNode) => matchingIds !== null && !matchingIds.has(d.id),
    );
  }, [selected, matchingIds]);

  if (nodes.length === 0) {
    return (
      <div class="graph-view__empty">
        <span>No concepts to display</span>
      </div>
    );
  }

  return <svg ref={svgRef} class="graph-view" />;
}
