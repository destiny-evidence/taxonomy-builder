import { ontologyGraphData } from "../../state/ontologyGraph";
import type { OntologyGraphNode, OntologyGraphEdge } from "../../state/ontologyGraph";
import "./OntologyGraph.css";

function nodeTooltip(node: OntologyGraphNode): string {
  const parts = [node.label];
  if (node.comment) parts.push(node.comment);
  if (node.description) parts.push(node.description);
  return parts.join("\n");
}

function edgeTooltip(edge: OntologyGraphEdge): string {
  const parts = [edge.label];
  if (edge.description) parts.push(edge.description);
  const meta: string[] = [];
  if (edge.required) meta.push("required");
  if (edge.cardinality) meta.push(edge.cardinality);
  if (meta.length > 0) parts.push(meta.join(", "));
  return parts.join("\n");
}

function NodeRect({ node }: { node: OntologyGraphNode }) {
  const dimmed = !node.connected;
  const className = [
    "ontology-graph__node",
    `ontology-graph__node--${node.type}`,
    dimmed ? "ontology-graph__node--dimmed" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <g
      class={className}
      data-node-type={node.type}
      data-node-id={node.id}
      transform={`translate(${node.x}, ${node.y})`}
    >
      <title>{nodeTooltip(node)}</title>
      <rect
        width={node.width}
        height={node.height}
        rx={6}
        ry={6}
      />
      <text
        x={node.width / 2}
        y={node.height / 2}
        dominant-baseline="central"
        text-anchor="middle"
      >
        {node.label}
      </text>
    </g>
  );
}

function Edge({ edge, nodes }: { edge: OntologyGraphEdge; nodes: OntologyGraphNode[] }) {
  const source = nodes.find((n) => n.id === edge.sourceId);
  const target = nodes.find((n) => n.id === edge.targetId);
  if (!source || !target) return null;

  const x1 = source.x + source.width;
  const y1 = source.y + source.height / 2 + edge.parallelOffset;
  const x2 = target.x;
  const y2 = target.y + target.height / 2 + edge.parallelOffset;

  // Bezier control points for a gentle curve
  const midX = (x1 + x2) / 2;

  const labelX = x1 + 12;
  const labelY = y1 - 6;

  return (
    <g class="ontology-graph__edge" data-edge-id={edge.id}>
      <title>{edgeTooltip(edge)}</title>
      {/* Wide invisible hit target */}
      <path
        d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
        class="ontology-graph__edge-hit"
      />
      {/* Visible edge */}
      <path
        d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
        class="ontology-graph__edge-path"
      />
      <text
        x={labelX}
        y={labelY}
        class="ontology-graph__edge-label"
        data-edge-label
      >
        {edge.label}
      </text>
    </g>
  );
}

function Legend() {
  return (
    <g class="ontology-graph__legend" transform="translate(16, 8)">
      {/* Class */}
      <rect x={0} y={0} width={12} height={12} rx={2} class="ontology-graph__legend-swatch ontology-graph__legend-swatch--class" />
      <text x={18} y={10} class="ontology-graph__legend-text">Class</text>

      {/* Scheme */}
      <rect x={70} y={0} width={12} height={12} rx={2} class="ontology-graph__legend-swatch ontology-graph__legend-swatch--scheme" />
      <text x={88} y={10} class="ontology-graph__legend-text">Scheme</text>

      {/* Datatype */}
      <rect x={152} y={0} width={12} height={12} rx={2} class="ontology-graph__legend-swatch ontology-graph__legend-swatch--datatype" />
      <text x={170} y={10} class="ontology-graph__legend-text">Datatype</text>

      {/* Dimmed */}
      <rect x={244} y={0} width={12} height={12} rx={2} class="ontology-graph__legend-swatch ontology-graph__legend-swatch--dimmed" />
      <text x={262} y={10} class="ontology-graph__legend-text">unconnected</text>
    </g>
  );
}

export function OntologyGraph() {
  const data = ontologyGraphData.value;

  if (!data) {
    return (
      <div class="ontology-graph ontology-graph--empty">
        <p class="ontology-graph__message">No core ontology loaded</p>
      </div>
    );
  }

  return (
    <div class="ontology-graph">
      <svg
        class="ontology-graph__svg"
        viewBox={`0 0 ${data.width} ${data.height}`}
        preserveAspectRatio="xMidYMin meet"
      >
        <Legend />

        {data.edges.map((edge) => (
          <Edge key={edge.id} edge={edge} nodes={data.nodes} />
        ))}

        {data.nodes.map((node) => (
          <NodeRect key={node.id} node={node} />
        ))}
      </svg>
    </div>
  );
}
