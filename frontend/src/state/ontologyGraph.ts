import { computed } from "@preact/signals";
import { ontologyClasses, ontology, selectedClassUri } from "./ontology";
import { properties } from "./properties";
import { schemes } from "./schemes";
import type { OntologyClass, OntologyProperty, Property, ConceptScheme } from "../types/models";

// ============================================================
// Types
// ============================================================

export type NodeZone = "selected" | "hub" | "spoke" | "disconnected" | "fan";
export type EdgeKind = "property" | "structural" | "spoke";

export interface OntologyGraphNode {
  id: string;
  label: string;
  type: "class" | "scheme";
  zone: NodeZone;
  shape: "rect" | "hexagon";
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
  kind: EdgeKind;
  description: string | null;
  required: boolean;
  cardinality: "single" | "multiple";
  parallelOffset: number;
}

export interface FanSchemeCard {
  schemeId: string;
  schemeTitle: string;
  schemeDescription: string | null;
  propertyLabels: string[];
}

export interface OntologyGraphData {
  nodes: OntologyGraphNode[];
  edges: OntologyGraphEdge[];
  fanSchemes: FanSchemeCard[];
  width: number;
  height: number;
}

// ============================================================
// Internal types for structural edges
// ============================================================

export interface StructuralEdge {
  id: string;
  sourceUri: string;
  targetUri: string;
  label: string;
  propertyUri: string;
}

// ============================================================
// Layout constants
// ============================================================

const NODE_WIDTH = 140;
const NODE_HEIGHT = 36;
const HEXAGON_MIN_WIDTH = 120;
const HEXAGON_CHAR_WIDTH = 7.5;
const HEXAGON_PADDING = 28;
const HEXAGON_HEIGHT = 34;
const GRAPH_PADDING = 20;
const MIN_FAN_RADIUS = 120;
const FAN_GAP = 16; // minimum gap between adjacent hexagons
const SELECTED_Y = 20;
const HUB_Y = 200;
const SPOKE_Y = 360;
const SPOKE_SPACING_X = 150;

const FINDING_LABEL = "Finding";
const FAN_ARC_THRESHOLD = 0; // always use grid layout
const FAN_GRID_COL_GAP = 14;
const FAN_GRID_ROW_GAP = 40; // includes space for label below hexagon
const FAN_GRID_MAX_COLS = 4;

/** Compute hexagon width to fit its label text. */
function hexWidth(label: string): number {
  return Math.max(HEXAGON_MIN_WIDTH, label.length * HEXAGON_CHAR_WIDTH + HEXAGON_PADDING);
}

/** Compute fan radius so adjacent hexagons don't overlap on the arc. */
function computeFanRadius(hexWidths: number[], arcSpan: number): number {
  if (hexWidths.length <= 1) return MIN_FAN_RADIUS;
  const angularSep = arcSpan / (hexWidths.length - 1);
  let maxNeeded = MIN_FAN_RADIUS;
  for (let i = 0; i < hexWidths.length - 1; i++) {
    const neededChord = (hexWidths[i] + hexWidths[i + 1]) / 2 + FAN_GAP;
    const sinHalf = Math.sin(angularSep / 2);
    if (sinHalf > 0.01) {
      const r = neededChord / (2 * sinHalf);
      if (r > maxNeeded) maxNeeded = r;
    }
  }
  return maxNeeded;
}

// ============================================================
// Helper Functions
// ============================================================

/**
 * Extract structural edges (class↔class) from object properties.
 * Deduplicates inverse property pairs. Expands union domains.
 * Only includes edges where both source and target are known classes.
 */
export function extractStructuralEdges(
  objectProperties: OntologyProperty[],
  knownClassUris: Set<string>
): StructuralEdge[] {
  // Build a set of edges, keyed by sorted [source, target] to detect inverses
  const edgeMap = new Map<string, StructuralEdge>();

  for (const prop of objectProperties) {
    const domains = prop.domain.filter((d) => knownClassUris.has(d));
    const ranges = prop.range.filter((r) => knownClassUris.has(r));

    for (const domain of domains) {
      for (const range of ranges) {
        if (domain === range) continue;

        // Canonical key: sorted pair so inverses collide
        const pairKey = [domain, range].sort().join("::");
        if (edgeMap.has(pairKey)) continue; // keep first-encountered direction

        edgeMap.set(pairKey, {
          id: `structural::${prop.uri}::${domain}::${range}`,
          sourceUri: domain,
          targetUri: range,
          label: prop.label,
          propertyUri: prop.uri,
        });
      }
    }
  }

  return [...edgeMap.values()];
}

/**
 * Find the hub class — prefers "Finding", falls back to most-connected class.
 */
export function findHubClass(
  classes: OntologyClass[],
  structuralEdges: StructuralEdge[]
): string | null {
  if (classes.length === 0) return null;

  // Prefer Finding
  const finding = classes.find((c) => c.label === FINDING_LABEL);
  if (finding) return finding.uri;

  // Fallback: most-connected class
  const connectionCount = new Map<string, number>();
  for (const c of classes) connectionCount.set(c.uri, 0);
  for (const edge of structuralEdges) {
    connectionCount.set(edge.sourceUri, (connectionCount.get(edge.sourceUri) ?? 0) + 1);
    connectionCount.set(edge.targetUri, (connectionCount.get(edge.targetUri) ?? 0) + 1);
  }

  let bestUri = classes[0].uri;
  let bestCount = connectionCount.get(bestUri) ?? 0;
  for (const c of classes) {
    const count = connectionCount.get(c.uri) ?? 0;
    if (count > bestCount) {
      bestUri = c.uri;
      bestCount = count;
    }
  }
  return bestUri;
}

/**
 * Find the structural edge connecting selected and hub (in either direction).
 */
export function findHubEdge(
  selectedUri: string,
  hubUri: string,
  structuralEdges: StructuralEdge[]
): StructuralEdge | null {
  return (
    structuralEdges.find(
      (e) =>
        (e.sourceUri === selectedUri && e.targetUri === hubUri) ||
        (e.sourceUri === hubUri && e.targetUri === selectedUri)
    ) ?? null
  );
}

// ============================================================
// Layout Engine
// ============================================================

/**
 * Build the full carousel layout from data.
 */
export function buildCarouselLayout(
  selectedUri: string,
  classes: OntologyClass[],
  objectProperties: OntologyProperty[],
  projectProperties: Property[],
  projectSchemes: ConceptScheme[]
): OntologyGraphData {
  const knownClassUris = new Set(classes.map((c) => c.uri));
  const structuralEdges = extractStructuralEdges(objectProperties, knownClassUris);
  const hubUri = findHubClass(classes, structuralEdges);
  const isHubSelected = selectedUri === hubUri;

  // --- Classify nodes into zones ---
  const hubConnected = new Set<string>();
  if (hubUri && !isHubSelected) {
    for (const edge of structuralEdges) {
      if (edge.sourceUri === hubUri) hubConnected.add(edge.targetUri);
      if (edge.targetUri === hubUri) hubConnected.add(edge.sourceUri);
    }
  } else if (isHubSelected) {
    // When hub (Finding) is selected, all connected classes are spokes
    for (const edge of structuralEdges) {
      if (edge.sourceUri === selectedUri) hubConnected.add(edge.targetUri);
      if (edge.targetUri === selectedUri) hubConnected.add(edge.sourceUri);
    }
  }

  // Remove selected from hub-connected (it's in its own zone)
  hubConnected.delete(selectedUri);
  if (hubUri) hubConnected.delete(hubUri);

  // Build class nodes with zones
  const classZone = new Map<string, NodeZone>();
  for (const c of classes) {
    if (c.uri === selectedUri) {
      classZone.set(c.uri, "selected");
    } else if (!isHubSelected && c.uri === hubUri) {
      classZone.set(c.uri, "hub");
    } else if (hubConnected.has(c.uri)) {
      classZone.set(c.uri, "spoke");
    } else {
      classZone.set(c.uri, "disconnected");
    }
  }

  // --- Fan: project properties targeting schemes for the selected class ---
  const fanProperties = projectProperties.filter(
    (p) => p.domain_class === selectedUri && p.range_scheme_id
  );
  const fanSchemeIds = new Set(fanProperties.map((p) => p.range_scheme_id!));
  const schemeMap = new Map(projectSchemes.map((s) => [s.id, s]));

  // --- Position nodes ---
  const nodes: OntologyGraphNode[] = [];
  const selectedClass = classes.find((c) => c.uri === selectedUri);

  // Determine fan geometry dynamically
  const spokeClasses = classes.filter((c) => classZone.get(c.uri) === "spoke");
  const disconnectedClasses = classes.filter((c) => classZone.get(c.uri) === "disconnected");
  const fanSchemeList = [...fanSchemeIds].map((id) => schemeMap.get(id)).filter(Boolean) as ConceptScheme[];
  const fanHexWidths = fanSchemeList.map((s) => hexWidth(s.title));
  const useArc = fanSchemeList.length > 0 && fanSchemeList.length <= FAN_ARC_THRESHOLD;

  // Arc geometry (only used for ≤4 items)
  const ARC_START = (5 * Math.PI) / 6; // 150°
  const ARC_END = Math.PI / 6;         // 30°
  const ARC_SPAN = ARC_START - ARC_END;
  const fanRadius = useArc ? computeFanRadius(fanHexWidths, ARC_SPAN) : MIN_FAN_RADIUS;

  // Grid geometry (used for 5+ items)
  const maxHexW = fanHexWidths.length > 0 ? Math.max(...fanHexWidths) : 0;
  let fanZoneWidth = 0;
  let fanZoneHeight = MIN_FAN_RADIUS + HEXAGON_HEIGHT + 20; // default reserve

  if (useArc) {
    fanZoneWidth = fanRadius * 2 + maxHexW;
    fanZoneHeight = fanRadius + HEXAGON_HEIGHT + 20;
  } else if (fanSchemeList.length > 0) {
    // Grid: compute rows
    const cols = Math.min(fanSchemeList.length, FAN_GRID_MAX_COLS);
    fanZoneWidth = cols * (maxHexW + FAN_GRID_COL_GAP) - FAN_GRID_COL_GAP;
    const rows = Math.ceil(fanSchemeList.length / FAN_GRID_MAX_COLS);
    fanZoneHeight = rows * (HEXAGON_HEIGHT + FAN_GRID_ROW_GAP) + 10;
  }

  // Determine center X based on widest layer
  const widestRowCount = Math.max(spokeClasses.length, disconnectedClasses.length);
  const bottomWidth = widestRowCount * SPOKE_SPACING_X;
  const graphWidth = Math.max(bottomWidth, fanZoneWidth, NODE_WIDTH * 2) + GRAPH_PADDING * 2;
  const centerX = graphWidth / 2;

  const FAN_ZONE_HEIGHT = fanZoneHeight;

  // Selected class node
  if (selectedClass) {
    nodes.push({
      id: selectedClass.uri,
      label: selectedClass.label,
      type: "class",
      zone: "selected",
      shape: "rect",
      x: centerX - NODE_WIDTH / 2,
      y: SELECTED_Y + FAN_ZONE_HEIGHT,
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      comment: selectedClass.comment,
    });
  }

  // Fan hexagon nodes
  if (fanSchemeList.length > 0 && selectedClass) {
    if (useArc) {
      // Semicircle arc for ≤4 items
      const selectedNodeY = SELECTED_Y + fanRadius + HEXAGON_HEIGHT + 20;
      const fanCenterX = centerX;
      const fanCenterY = selectedNodeY;

      for (let i = 0; i < fanSchemeList.length; i++) {
        const scheme = fanSchemeList[i];
        const hw = fanHexWidths[i];
        const count = fanSchemeList.length;
        const angle = count === 1
          ? Math.PI / 2
          : ARC_START - (i / (count - 1)) * ARC_SPAN;
        const fx = fanCenterX + Math.cos(angle) * fanRadius - hw / 2;
        const fy = fanCenterY - Math.sin(angle) * fanRadius - HEXAGON_HEIGHT / 2;

        nodes.push({
          id: scheme.id,
          label: scheme.title,
          type: "scheme",
          zone: "fan",
          shape: "hexagon",
          x: fx,
          y: fy,
          width: hw,
          height: HEXAGON_HEIGHT,
          description: scheme.description,
        });
      }
    } else {
      // Grid layout for 5+ items — centered rows above selected node
      for (let i = 0; i < fanSchemeList.length; i++) {
        const scheme = fanSchemeList[i];
        const hw = fanHexWidths[i];
        const row = Math.floor(i / FAN_GRID_MAX_COLS);
        const col = i % FAN_GRID_MAX_COLS;
        // How many items in this row?
        const itemsInRow = Math.min(FAN_GRID_MAX_COLS, fanSchemeList.length - row * FAN_GRID_MAX_COLS);
        const thisRowWidth = itemsInRow * (maxHexW + FAN_GRID_COL_GAP) - FAN_GRID_COL_GAP;

        const fx = centerX - thisRowWidth / 2 + col * (maxHexW + FAN_GRID_COL_GAP) + (maxHexW - hw) / 2;
        const fy = SELECTED_Y + row * (HEXAGON_HEIGHT + FAN_GRID_ROW_GAP);

        nodes.push({
          id: scheme.id,
          label: scheme.title,
          type: "scheme",
          zone: "fan",
          shape: "hexagon",
          x: fx,
          y: fy,
          width: hw,
          height: HEXAGON_HEIGHT,
          description: scheme.description,
        });
      }
    }
  }

  // Hub node
  const hubClass = !isHubSelected && hubUri ? classes.find((c) => c.uri === hubUri) : null;
  const actualHubY = HUB_Y + FAN_ZONE_HEIGHT;
  if (hubClass) {
    nodes.push({
      id: hubClass.uri,
      label: hubClass.label,
      type: "class",
      zone: "hub",
      shape: "rect",
      x: centerX - NODE_WIDTH / 2,
      y: actualHubY,
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      comment: hubClass.comment,
    });
  }

  // Spoke nodes (centered row)
  const actualSpokeY = SPOKE_Y + FAN_ZONE_HEIGHT;
  const spokeStartX = centerX - ((spokeClasses.length - 1) * SPOKE_SPACING_X) / 2;

  for (let i = 0; i < spokeClasses.length; i++) {
    const c = spokeClasses[i];
    nodes.push({
      id: c.uri,
      label: c.label,
      type: "class",
      zone: "spoke",
      shape: "rect",
      x: spokeStartX + i * SPOKE_SPACING_X - NODE_WIDTH / 2,
      y: actualSpokeY,
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      comment: c.comment,
    });
  }

  // Disconnected nodes (separate centered row below spokes)
  if (disconnectedClasses.length > 0) {
    const disconnectedY = actualSpokeY + NODE_HEIGHT + 40;
    const disconnectedStartX = centerX - ((disconnectedClasses.length - 1) * SPOKE_SPACING_X) / 2;

    for (let i = 0; i < disconnectedClasses.length; i++) {
      const c = disconnectedClasses[i];
      nodes.push({
        id: c.uri,
        label: c.label,
        type: "class",
        zone: "disconnected",
        shape: "rect",
        x: disconnectedStartX + i * SPOKE_SPACING_X - NODE_WIDTH / 2,
        y: disconnectedY,
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
        comment: c.comment,
      });
    }
  }

  // --- Build edges ---
  const edges: OntologyGraphEdge[] = [];

  // Structural edge: selected ↔ hub
  if (hubUri && !isHubSelected) {
    const hubEdge = findHubEdge(selectedUri, hubUri, structuralEdges);
    if (hubEdge) {
      edges.push({
        id: hubEdge.id,
        sourceId: selectedUri,
        targetId: hubUri,
        label: hubEdge.label,
        kind: "structural",
        description: null,
        required: false,
        cardinality: "single",
        parallelOffset: 0,
      });
    }
  }

  // Spoke edges: hub ↔ spoke classes
  const spokeSourceUri = isHubSelected ? selectedUri : hubUri;
  if (spokeSourceUri) {
    for (const spoke of spokeClasses) {
      const spokeEdge = structuralEdges.find(
        (e) =>
          (e.sourceUri === spokeSourceUri && e.targetUri === spoke.uri) ||
          (e.sourceUri === spoke.uri && e.targetUri === spokeSourceUri)
      );
      if (spokeEdge) {
        edges.push({
          id: `spoke::${spokeEdge.id}`,
          sourceId: spokeSourceUri,
          targetId: spoke.uri,
          label: spokeEdge.label,
          kind: "spoke",
          description: null,
          required: false,
          cardinality: "single",
          parallelOffset: 0,
        });
      }
    }
  }

  // Fan/property edges: selected → scheme hexagons
  for (const prop of fanProperties) {
    if (!prop.range_scheme_id) continue;
    edges.push({
      id: `property::${prop.id}`,
      sourceId: selectedUri,
      targetId: prop.range_scheme_id,
      label: prop.label,
      kind: "property",
      description: prop.description,
      required: prop.required,
      cardinality: prop.cardinality,
      parallelOffset: 0,
    });
  }

  // Build fan scheme cards (group properties by scheme)
  const fanSchemeCardMap = new Map<string, FanSchemeCard>();
  for (const prop of fanProperties) {
    if (!prop.range_scheme_id) continue;
    const scheme = schemeMap.get(prop.range_scheme_id);
    if (!scheme) continue;
    const existing = fanSchemeCardMap.get(scheme.id);
    if (existing) {
      existing.propertyLabels.push(prop.label);
    } else {
      fanSchemeCardMap.set(scheme.id, {
        schemeId: scheme.id,
        schemeTitle: scheme.title,
        schemeDescription: scheme.description,
        propertyLabels: [prop.label],
      });
    }
  }
  const fanSchemes = [...fanSchemeCardMap.values()];

  // Compute bounding box
  let maxY = 0;
  for (const n of nodes) {
    const bottom = n.y + n.height;
    if (bottom > maxY) maxY = bottom;
  }

  return {
    nodes,
    edges,
    fanSchemes,
    width: graphWidth,
    height: maxY + GRAPH_PADDING,
  };
}

// ============================================================
// Computed Signal
// ============================================================

export const carouselGraphData = computed<OntologyGraphData | null>(() => {
  if (!ontology.value || !selectedClassUri.value) return null;

  return buildCarouselLayout(
    selectedClassUri.value,
    ontologyClasses.value,
    ontology.value.object_properties,
    properties.value,
    schemes.value
  );
});
