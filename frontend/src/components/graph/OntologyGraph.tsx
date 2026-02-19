import { carouselGraphData } from "../../state/ontologyGraph";
import { selectedClassUri, ontology } from "../../state/ontology";
import type { OntologyGraphNode, OntologyGraphEdge, NodeZone, FanSchemeCard } from "../../state/ontologyGraph";
import "./OntologyGraph.css";

const ZONE_OPACITY: Record<NodeZone, number> = {
  selected: 1,
  hub: 0.85,
  spoke: 0.75,
  disconnected: 0.6,
  fan: 1,
};

function nodeTooltip(node: OntologyGraphNode): string {
  const parts = [node.label];
  if (node.comment) parts.push(node.comment);
  if (node.description) parts.push(node.description);
  return parts.join("\n");
}

function hexagonPoints(w: number, h: number): string {
  // Flat-top hexagon
  const dx = h / (2 * Math.sqrt(3));
  return [
    `${dx},0`,
    `${w - dx},0`,
    `${w},${h / 2}`,
    `${w - dx},${h}`,
    `${dx},${h}`,
    `0,${h / 2}`,
  ].join(" ");
}

function NodeShape({ node, onSchemeNavigate }: { node: OntologyGraphNode; onSchemeNavigate?: (schemeId: string) => void }) {
  const isClickable = node.type === "class" || node.type === "scheme";
  const opacity = ZONE_OPACITY[node.zone];
  const className = [
    "ontology-graph__node",
    `ontology-graph__node--${node.type}`,
    `ontology-graph__node--${node.zone}`,
    isClickable ? "ontology-graph__node--clickable" : "",
  ]
    .filter(Boolean)
    .join(" ");

  function handleClick() {
    if (node.type === "class") {
      selectedClassUri.value = node.id;
    } else if (node.type === "scheme") {
      onSchemeNavigate?.(node.id);
    }
  }

  return (
    <g
      class={className}
      data-node-type={node.type}
      data-node-id={node.id}
      data-zone={node.zone}
      data-shape={node.shape}
      transform={`translate(${node.x}, ${node.y})`}
      style={{ opacity }}
      onClick={handleClick}
    >
      <title>{nodeTooltip(node)}</title>
      {node.shape === "hexagon" ? (
        <polygon points={hexagonPoints(node.width, node.height)} />
      ) : (
        <rect width={node.width} height={node.height} rx={6} ry={6} />
      )}
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

function EdgePath({ edge, nodes }: { edge: OntologyGraphEdge; nodes: OntologyGraphNode[] }) {
  const source = nodes.find((n) => n.id === edge.sourceId);
  const target = nodes.find((n) => n.id === edge.targetId);
  if (!source || !target) return null;

  const x1 = source.x + source.width / 2;
  const y1 = source.y + source.height;
  const x2 = target.x + target.width / 2;
  const y2 = target.y;

  let pathD: string;
  if (edge.kind === "spoke") {
    // Curved bezier for spokes
    const cpY = (y1 + y2) / 2;
    pathD = `M ${x1} ${y1} C ${x1} ${cpY}, ${x2} ${cpY}, ${x2} ${y2}`;
  } else {
    // Straight line for structural and property edges
    pathD = `M ${x1} ${y1} L ${x2} ${y2}`;
  }

  const edgeOpacity = edge.kind === "spoke" ? 0.65 : 0.8;

  // Label position — fan labels below their hexagon, spoke labels near target,
  // structural labels at midpoint
  let labelX: number;
  let labelY: number;
  if (edge.kind === "property") {
    // Place label just below the target hexagon
    labelX = target.x + target.width / 2;
    labelY = target.y + target.height + 20;
  } else {
    const labelT = edge.kind === "spoke" ? 0.65 : 0.5;
    labelX = x1 + (x2 - x1) * labelT;
    labelY = y1 + (y2 - y1) * labelT;
  }

  return (
    <g
      class={`ontology-graph__edge ontology-graph__edge--${edge.kind}`}
      data-edge-kind={edge.kind}
      data-edge-id={edge.id}
    >
      <path d={pathD} class="ontology-graph__edge-path" style={{ opacity: edgeOpacity }} />
      <g
        class="ontology-graph__edge-label-chip"
        transform={`translate(${labelX}, ${labelY})`}
        data-edge-label
      >
        {edge.kind !== "property" && (() => {
          const chipW = Math.max(60, edge.label.length * 6.5 + 14);
          return <rect x={-chipW / 2} y={-11} width={chipW} height={20} rx={7} />;
        })()}
        <text x={0} y={0} class="ontology-graph__edge-label" text-anchor="middle">
          {edge.label}
        </text>
      </g>
    </g>
  );
}

function SchemeCard({
  card,
  onNavigate,
}: {
  card: FanSchemeCard;
  onNavigate?: (schemeId: string) => void;
}) {
  return (
    <div
      class="ontology-graph__card"
      onClick={() => onNavigate?.(card.schemeId)}
      data-scheme-id={card.schemeId}
    >
      <div class="ontology-graph__card-title">{card.schemeTitle}</div>
      <div class="ontology-graph__card-meta">
        {card.propertyLabels.join(", ")}
      </div>
      {card.schemeDescription ? (
        <div class="ontology-graph__card-description">{card.schemeDescription}</div>
      ) : null}
    </div>
  );
}

interface OntologyGraphProps {
  onSchemeNavigate?: (schemeId: string) => void;
}

export function OntologyGraph({ onSchemeNavigate }: OntologyGraphProps) {
  const data = carouselGraphData.value;

  if (!data) {
    // Determine which empty state to show
    let message: string;
    if (!ontology.value) {
      message = "No core ontology loaded";
    } else if (!selectedClassUri.value) {
      message = "Select a class to view the ontology graph";
    } else {
      message = "Loading ontology...";
    }
    return (
      <div class="ontology-graph ontology-graph--empty">
        <p class="ontology-graph__message">{message}</p>
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
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 6"
            refX="10"
            refY="3"
            markerWidth="8"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 3 L 0 6 Z" fill="var(--color-border)" />
          </marker>
        </defs>

        {data.edges.map((edge) => (
          <EdgePath key={edge.id} edge={edge} nodes={data.nodes} />
        ))}

        {data.nodes.map((node) => (
          <NodeShape key={node.id} node={node} />
        ))}
      </svg>

      {data.fanSchemes.length > 0 ? (
        <div class="ontology-graph__cards">
          <div class="ontology-graph__cards-label">Concept Schemes</div>
          <div class="ontology-graph__card-grid">
            {data.fanSchemes.map((card) => (
              <SchemeCard
                key={card.schemeId}
                card={card}
                onNavigate={onSchemeNavigate}
              />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
