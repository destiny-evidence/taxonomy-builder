import { computed } from "@preact/signals";
import { ontologyClasses, ontology } from "./ontology";
import { properties } from "./properties";
import { schemes } from "./schemes";
import { datatypeLabel } from "../types/models";

// Layout constants
const LEFT_COLUMN_X = 40;
const RIGHT_COLUMN_X = 520;
const NODE_START_Y = 44;
const NODE_SPACING_Y = 56;
const NODE_WIDTH = 188;
const NODE_HEIGHT = 36;
const DATATYPE_NODE_WIDTH = 148;
const DATATYPE_NODE_HEIGHT = 30;
const PARALLEL_EDGE_GAP = 14;

export interface OntologyGraphNode {
  id: string;
  label: string;
  type: "class" | "scheme" | "datatype";
  connected: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
  comment?: string | null;
  description?: string | null;
}

export interface OntologyGraphEdge {
  id: string;
  sourceId: string;
  targetId: string;
  label: string;
  description: string | null;
  required: boolean;
  cardinality: "single" | "multiple";
  parallelOffset: number;
}

export interface OntologyGraphData {
  nodes: OntologyGraphNode[];
  edges: OntologyGraphEdge[];
  width: number;
  height: number;
}

export const ontologyGraphData = computed<OntologyGraphData | null>(() => {
  if (!ontology.value) return null;

  const classes = ontologyClasses.value;
  const projectProperties = properties.value;
  const projectSchemes = schemes.value;

  // Collect IDs of nodes that have at least one edge
  const connectedIds = new Set<string>();
  for (const prop of projectProperties) {
    connectedIds.add(prop.domain_class);
    if (prop.range_scheme_id) connectedIds.add(prop.range_scheme_id);
    if (prop.range_datatype) connectedIds.add(prop.range_datatype);
  }

  // Left column: class nodes in backend order (matches ProjectPane)
  const knownClassUris = new Set(classes.map((c) => c.uri));

  const classNodes: OntologyGraphNode[] = classes.map((c, i) => ({
    id: c.uri,
    label: c.label,
    type: "class",
    connected: connectedIds.has(c.uri),
    x: LEFT_COLUMN_X,
    y: NODE_START_Y + i * NODE_SPACING_Y,
    width: NODE_WIDTH,
    height: NODE_HEIGHT,
    comment: c.comment,
  }));

  // Synthetic class nodes for unknown domain_class URIs
  const syntheticClasses: OntologyGraphNode[] = [];
  for (const prop of projectProperties) {
    if (!knownClassUris.has(prop.domain_class) && !syntheticClasses.some((n) => n.id === prop.domain_class)) {
      syntheticClasses.push({
        id: prop.domain_class,
        label: prop.domain_class,
        type: "class",
        connected: true,
        x: LEFT_COLUMN_X,
        y: NODE_START_Y + (classNodes.length + syntheticClasses.length) * NODE_SPACING_Y,
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
        comment: null,
      });
    }
  }

  const allClassNodes = [...classNodes, ...syntheticClasses];

  // Right column: scheme nodes
  const schemeNodes: OntologyGraphNode[] = projectSchemes.map((s) => ({
    id: s.id,
    label: s.title,
    type: "scheme",
    connected: connectedIds.has(s.id),
    x: RIGHT_COLUMN_X,
    y: 0,
    width: NODE_WIDTH,
    height: NODE_HEIGHT,
    description: s.description,
  }));

  // Right column: datatype nodes (only referenced ones)
  const referencedDatatypes = new Set<string>();
  for (const prop of projectProperties) {
    if (prop.range_datatype) referencedDatatypes.add(prop.range_datatype);
  }

  const datatypeNodes: OntologyGraphNode[] = [...referencedDatatypes].sort().map((dt) => ({
    id: dt,
    label: datatypeLabel(dt),
    type: "datatype",
    connected: true,
    x: RIGHT_COLUMN_X + (NODE_WIDTH - DATATYPE_NODE_WIDTH),
    y: 0,
    width: DATATYPE_NODE_WIDTH,
    height: DATATYPE_NODE_HEIGHT,
  }));

  // Spread class rows to use the available graph height when the right column is denser.
  const targetRowCount = Math.max(
    allClassNodes.length,
    schemeNodes.length + datatypeNodes.length
  );
  const leftSpacingY = allClassNodes.length > 1
    ? Math.max(
      NODE_SPACING_Y,
      ((targetRowCount - 1) * NODE_SPACING_Y) / (allClassNodes.length - 1)
    )
    : NODE_SPACING_Y;
  for (let i = 0; i < allClassNodes.length; i++) {
    allClassNodes[i].y = NODE_START_Y + i * leftSpacingY;
  }

  // Order right column by average Y of connected left-side nodes, alphabetical tiebreak
  const leftNodeYMap = new Map<string, number>();
  for (const node of allClassNodes) {
    leftNodeYMap.set(node.id, node.y);
  }

  function averageConnectedY(rightId: string): number {
    const ys: number[] = [];
    for (const prop of projectProperties) {
      const leftY = leftNodeYMap.get(prop.domain_class);
      if (leftY === undefined) continue;
      if (prop.range_scheme_id === rightId || prop.range_datatype === rightId) {
        ys.push(leftY);
      }
    }
    return ys.length === 0 ? Infinity : ys.reduce((a, b) => a + b, 0) / ys.length;
  }

  const rightNodes = [...schemeNodes, ...datatypeNodes].sort((a, b) => {
    const aY = averageConnectedY(a.id);
    const bY = averageConnectedY(b.id);
    if (aY !== bY) return aY - bY;
    return a.label.localeCompare(b.label);
  });

  // Match right-column height to the stretched left-column height, with a minimum spacing.
  const leftColumnHeight = allClassNodes.length > 1
    ? (allClassNodes.length - 1) * leftSpacingY + NODE_HEIGHT
    : NODE_HEIGHT;
  const leftColumnSpan = Math.max(NODE_HEIGHT, leftColumnHeight - NODE_HEIGHT);
  const rightSpacingY = rightNodes.length > 1
    ? Math.max(NODE_HEIGHT + 4, leftColumnSpan / (rightNodes.length - 1))
    : NODE_SPACING_Y;

  for (let i = 0; i < rightNodes.length; i++) {
    rightNodes[i].y = NODE_START_Y + i * rightSpacingY;
  }

  // Edges with parallel offset detection
  const edgeGroups = new Map<string, string[]>();
  const rawEdges: Array<Omit<OntologyGraphEdge, "parallelOffset">> = [];

  for (const prop of projectProperties) {
    const targetId = prop.range_scheme_id ?? prop.range_datatype;
    if (!targetId) continue;

    const groupKey = `${prop.domain_class}::${targetId}`;
    if (!edgeGroups.has(groupKey)) edgeGroups.set(groupKey, []);
    edgeGroups.get(groupKey)!.push(prop.id);

    rawEdges.push({
      id: prop.id,
      sourceId: prop.domain_class,
      targetId,
      label: prop.label,
      description: prop.description,
      required: prop.required,
      cardinality: prop.cardinality,
    });
  }

  const edges: OntologyGraphEdge[] = rawEdges.map((raw) => {
    const group = edgeGroups.get(`${raw.sourceId}::${raw.targetId}`)!;
    const indexInGroup = group.indexOf(raw.id);
    const groupSize = group.length;

    let parallelOffset = 0;
    if (groupSize > 1) {
      const half = (groupSize - 1) / 2;
      parallelOffset = (indexInGroup - half) * PARALLEL_EDGE_GAP;
    }

    return { ...raw, parallelOffset };
  });

  const allNodes = [...allClassNodes, ...rightNodes];
  const maxY = allNodes.length > 0
    ? Math.max(...allNodes.map((n) => n.y + n.height))
    : 0;

  return {
    nodes: allNodes,
    edges,
    width: RIGHT_COLUMN_X + NODE_WIDTH + 40,
    height: maxY + NODE_START_Y,
  };
});
