import { useEffect, useRef, useState } from "preact/hooks";
import { ontologyGraphData } from "../../state/ontologyGraph";
import type { OntologyGraphNode, OntologyGraphEdge } from "../../state/ontologyGraph";
import "./OntologyGraph.css";

function nodeTooltip(node: OntologyGraphNode): string {
  const parts = [node.label];
  if (node.comment) parts.push(node.comment);
  if (node.description) parts.push(node.description);
  return parts.join("\n");
}

function edgeTooltipParts(edge: OntologyGraphEdge): {
  title: string;
  description?: string;
  meta: string[];
} {
  const meta: string[] = [];
  if (edge.required) meta.push("required");
  if (edge.cardinality === "multiple") meta.push("multiple values");
  return {
    title: edge.label,
    description: edge.description ?? undefined,
    meta,
  };
}

interface TooltipState {
  edgeId: string;
  title: string;
  description?: string;
  meta: string[];
  x: number;
  y: number;
  placeLeft: boolean;
  placeAbove: boolean;
}

function shortEdgeLabel(label: string): string {
  const compact = label.replace(/\s+/g, " ").trim();
  return compact.length <= 22 ? compact : `${compact.slice(0, 19)}...`;
}

function shortNodeLabel(label: string, maxChars: number): string {
  const compact = label.replace(/\s+/g, " ").trim();
  return compact.length <= maxChars ? compact : `${compact.slice(0, maxChars - 3)}...`;
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
  const labelMaxChars = node.type === "datatype" ? 18 : 24;
  const visibleLabel = shortNodeLabel(node.label, labelMaxChars);

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
        {visibleLabel}
      </text>
    </g>
  );
}

function Edge({
  edge,
  nodes,
  labelY,
  labelXOffset,
  activeEdgeId,
  onEdgeHover,
  onEdgeMove,
  onEdgeLeave,
}: {
  edge: OntologyGraphEdge;
  nodes: OntologyGraphNode[];
  labelY: number;
  labelXOffset: number;
  activeEdgeId: string | null;
  onEdgeHover: (edgeId: string, event: MouseEvent) => void;
  onEdgeMove: (edgeId: string, event: MouseEvent) => void;
  onEdgeLeave: (edgeId: string, event: MouseEvent) => void;
}) {
  const source = nodes.find((n) => n.id === edge.sourceId);
  const target = nodes.find((n) => n.id === edge.targetId);
  if (!source || !target) return null;

  const x1 = source.x + source.width;
  const y1 = source.y + source.height / 2 + edge.parallelOffset;
  const x2 = target.x;
  const y2 = target.y + target.height / 2 + edge.parallelOffset;

  const midX = (x1 + x2) / 2;
  const pathD = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
  const labelText = shortEdgeLabel(edge.label);
  const labelWidth = Math.max(62, Math.min(206, 12 + labelText.length * 7));
  const labelX = x1 + 14 + labelXOffset;
  const isDimmed = activeEdgeId !== null && activeEdgeId !== edge.id;
  const isActive = activeEdgeId === edge.id;
  const className = [
    "ontology-graph__edge",
    isDimmed ? "ontology-graph__edge--dimmed" : "",
    isActive ? "ontology-graph__edge--active" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <g
      class={className}
      data-edge-id={edge.id}
      onMouseEnter={(event) => onEdgeHover(edge.id, event)}
      onMouseMove={(event) => onEdgeMove(edge.id, event)}
      onMouseLeave={(event) => onEdgeLeave(edge.id, event)}
    >
      <path d={pathD} class="ontology-graph__edge-hit" />
      <path d={pathD} class="ontology-graph__edge-path" />
      <g
        class="ontology-graph__edge-label-chip"
        transform={`translate(${labelX}, ${labelY})`}
        data-edge-label
      >
        <rect x={0} y={-12} width={labelWidth} height={20} rx={7} />
        <text x={9} y={-2} class="ontology-graph__edge-label" text-anchor="start">
          {labelText}
        </text>
      </g>
    </g>
  );
}

export function OntologyGraph() {
  const data = ontologyGraphData.value;
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const hoverEnterTimerRef = useRef<number | null>(null);
  const hoverLeaveTimerRef = useRef<number | null>(null);
  const [hoveredEdgeId, setHoveredEdgeId] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const HOVER_ENTER_DELAY_MS = 70;
  const HOVER_LEAVE_DELAY_MS = 120;
  const HOVER_MIN_X_SVG = 390;

  if (!data) {
    return (
      <div class="ontology-graph ontology-graph--empty">
        <p class="ontology-graph__message">No core ontology loaded</p>
      </div>
    );
  }

  const nodeMap = new Map<string, OntologyGraphNode>();
  for (const node of data.nodes) nodeMap.set(node.id, node);
  const edgeMap = new Map<string, OntologyGraphEdge>();
  for (const edge of data.edges) edgeMap.set(edge.id, edge);
  const activeEdgeId = hoveredEdgeId;
  const edgesForRender = [...data.edges].sort((a, b) => {
    if (activeEdgeId === null) return 0;
    if (a.id === activeEdgeId) return 1;
    if (b.id === activeEdgeId) return -1;
    return 0;
  });

  useEffect(() => {
    return () => {
      if (hoverEnterTimerRef.current !== null) {
        window.clearTimeout(hoverEnterTimerRef.current);
      }
      if (hoverLeaveTimerRef.current !== null) {
        window.clearTimeout(hoverLeaveTimerRef.current);
      }
    };
  }, []);

  // Compute label rails per source and resolve local collisions.
  const sourceGroups = new Map<string, OntologyGraphEdge[]>();
  for (const edge of data.edges) {
    if (!sourceGroups.has(edge.sourceId)) sourceGroups.set(edge.sourceId, []);
    sourceGroups.get(edge.sourceId)!.push(edge);
  }
  const edgeLabelY = new Map<string, number>();
  const sourceLabelXOffset = new Map<string, number>();
  const MIN_LABEL_GAP = 22;
  const LABEL_T = 0.35;
  const LABEL_X_JITTER = [-8, -3, 3, 8];

  const sortedSourceIds = [...sourceGroups.keys()].sort((a, b) => {
    const aY = nodeMap.get(a)?.y ?? 0;
    const bY = nodeMap.get(b)?.y ?? 0;
    return aY - bY;
  });
  for (let i = 0; i < sortedSourceIds.length; i++) {
    sourceLabelXOffset.set(sortedSourceIds[i], LABEL_X_JITTER[i % LABEL_X_JITTER.length]);
  }
  for (const [, groupEdges] of sourceGroups) {
    const sorted = [...groupEdges]
      .sort((a, b) => {
        const aTargetY = nodeMap.get(a.targetId)?.y ?? 0;
        const bTargetY = nodeMap.get(b.targetId)?.y ?? 0;
        if (aTargetY !== bTargetY) return aTargetY - bTargetY;
        return a.label.localeCompare(b.label);
      });

    const count = sorted.length;
    const laneCenter = (count - 1) / 2;

    const positioned = sorted.map((edge, i) => {
      const source = nodeMap.get(edge.sourceId)!;
      const target = nodeMap.get(edge.targetId)!;
      const y1 = source.y + source.height / 2 + edge.parallelOffset;
      const y2 = target.y + target.height / 2 + edge.parallelOffset;
      const laneOffset = (i - laneCenter) * 19 - 2;
      const it = 1 - LABEL_T;
      const rawY =
        it * it * it * y1 +
        3 * it * it * LABEL_T * y1 +
        3 * it * LABEL_T * LABEL_T * y2 +
        LABEL_T * LABEL_T * LABEL_T * y2 +
        laneOffset;
      return { edgeId: edge.id, y: Math.max(28, rawY) };
    });

    positioned.sort((a, b) => a.y - b.y);
    for (let i = 1; i < positioned.length; i++) {
      if (positioned[i].y < positioned[i - 1].y + MIN_LABEL_GAP) {
        positioned[i].y = positioned[i - 1].y + MIN_LABEL_GAP;
      }
    }
    for (const item of positioned) {
      edgeLabelY.set(item.edgeId, item.y);
    }
  }

  function updateTooltip(edgeId: string, event: MouseEvent) {
    const edge = edgeMap.get(edgeId);
    const rect = containerRef.current?.getBoundingClientRect();
    if (!edge || !rect) return;
    const parts = edgeTooltipParts(edge);
    const linesForWidth = [
      parts.title,
      ...(parts.description ? [parts.description] : []),
      ...(parts.meta.length > 0 ? [parts.meta.join("  ")] : []),
    ];
    const longestLine = linesForWidth.reduce(
      (max, line) => Math.max(max, line.length),
      0
    );
    const tooltipWidth = Math.min(320, Math.max(170, longestLine * 7.2 + 24));
    const margin = 14;
    const rawX = event.clientX - rect.left;
    const rawY = event.clientY - rect.top;
    const placeLeft = rawX > rect.width * 0.62;
    const placeAbove = rawY > rect.height * 0.66;
    // Clamp anchor point so transformed tooltip stays fully inside the pane.
    const minAnchorX = placeLeft ? tooltipWidth + margin : margin;
    const maxAnchorX = placeLeft ? rect.width - margin : rect.width - tooltipWidth - margin;
    const x = Math.max(minAnchorX, Math.min(maxAnchorX, rawX));
    const y = Math.max(margin, Math.min(rect.height - margin, rawY));
    setTooltip({
      edgeId,
      title: parts.title,
      description: parts.description,
      meta: parts.meta,
      x,
      y,
      placeLeft,
      placeAbove,
    });
  }

  function isInLeftHoverSuppressionZone(event: MouseEvent): boolean {
    const target = event.target as Element | null;
    if (target?.closest(".ontology-graph__edge-label-chip")) return false;
    const svg = svgRef.current;
    if (!svg) return false;
    const rect = svg.getBoundingClientRect();
    const viewBox = svg.viewBox.baseVal;
    if (!viewBox || rect.width <= 0 || rect.height <= 0) return false;

    // Map client coordinates into SVG space, respecting preserveAspectRatio.
    const scale = Math.min(rect.width / viewBox.width, rect.height / viewBox.height);
    const renderedWidth = viewBox.width * scale;
    const offsetX = (rect.width - renderedWidth) / 2;
    const svgX = (event.clientX - rect.left - offsetX) / scale;
    return svgX < HOVER_MIN_X_SVG;
  }

  return (
    <div class="ontology-graph" ref={containerRef}>
      <svg
        ref={svgRef}
        class="ontology-graph__svg"
        viewBox={`0 0 ${data.width} ${data.height}`}
        preserveAspectRatio="xMidYMin meet"
      >
        {edgesForRender.map((edge) => (
          <Edge
            key={edge.id}
            edge={edge}
            nodes={data.nodes}
            labelY={edgeLabelY.get(edge.id) ?? 28}
            labelXOffset={sourceLabelXOffset.get(edge.sourceId) ?? 0}
            activeEdgeId={activeEdgeId}
            onEdgeHover={(edgeId, event) => {
              if (isInLeftHoverSuppressionZone(event)) return;
              if (hoverLeaveTimerRef.current !== null) {
                window.clearTimeout(hoverLeaveTimerRef.current);
                hoverLeaveTimerRef.current = null;
              }
              if (hoverEnterTimerRef.current !== null) {
                window.clearTimeout(hoverEnterTimerRef.current);
              }
              hoverEnterTimerRef.current = window.setTimeout(() => {
                setHoveredEdgeId(edgeId);
                updateTooltip(edgeId, event);
              }, HOVER_ENTER_DELAY_MS);
            }}
            onEdgeMove={(edgeId, event) => {
              if (isInLeftHoverSuppressionZone(event)) {
                setHoveredEdgeId(null);
                setTooltip(null);
                return;
              }
              updateTooltip(edgeId, event);
            }}
            onEdgeLeave={(edgeId, event) =>
              {
                if (hoverEnterTimerRef.current !== null) {
                  window.clearTimeout(hoverEnterTimerRef.current);
                  hoverEnterTimerRef.current = null;
                }
                const nextTarget = event.relatedTarget as Element | null;
                const movingToAnotherEdge = !!nextTarget?.closest(".ontology-graph__edge");
                if (!movingToAnotherEdge) {
                  if (hoverLeaveTimerRef.current !== null) {
                    window.clearTimeout(hoverLeaveTimerRef.current);
                    hoverLeaveTimerRef.current = null;
                  }
                  setHoveredEdgeId((current) => (current === edgeId ? null : current));
                  setTooltip(null);
                  return;
                }
                if (hoverLeaveTimerRef.current !== null) {
                  window.clearTimeout(hoverLeaveTimerRef.current);
                }
                hoverLeaveTimerRef.current = window.setTimeout(() => {
                  setHoveredEdgeId((current) => {
                    if (current !== edgeId) return current;
                    setTooltip(null);
                    return null;
                  });
                }, HOVER_LEAVE_DELAY_MS);
              }
            }
          />
        ))}

        {data.nodes.map((node) => (
          <NodeRect key={node.id} node={node} />
        ))}
      </svg>
      {tooltip ? (
        <div
          class={[
            "ontology-graph__tooltip",
            tooltip.placeLeft ? "ontology-graph__tooltip--left" : "",
            tooltip.placeAbove ? "ontology-graph__tooltip--above" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          style={{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }}
        >
          <div class="ontology-graph__tooltip-title">{tooltip.title}</div>
          {tooltip.description ? (
            <div class="ontology-graph__tooltip-description">{tooltip.description}</div>
          ) : null}
          {tooltip.meta.length > 0 ? (
            <div class="ontology-graph__tooltip-meta">
              {tooltip.meta.map((item) => (
                <span key={`${tooltip.edgeId}-${item}`} class="ontology-graph__tooltip-tag">
                  {item}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
