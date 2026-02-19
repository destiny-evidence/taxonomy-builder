import { describe, it, expect, beforeEach } from "vitest";
import { ontology, selectedClassUri } from "../../src/state/ontology";
import { properties } from "../../src/state/properties";
import { schemes } from "../../src/state/schemes";
import {
  extractStructuralEdges,
  findHubClass,
  findHubEdge,
  buildCarouselLayout,
  carouselGraphData,
} from "../../src/state/ontologyGraph";
import type { CoreOntology, OntologyProperty, Property, ConceptScheme } from "../../src/types/models";

// --- Test Data ---

const INVESTIGATION = "http://example.org/Investigation";
const FINDING = "http://example.org/Finding";
const INTERVENTION = "http://example.org/Intervention";
const OUTCOME = "http://example.org/Outcome";
const CONTEXT = "http://example.org/Context";
const FUNDER = "http://example.org/Funder";
const IMPLEMENTER = "http://example.org/Implementer";

const essaClasses = [
  { uri: INVESTIGATION, label: "Investigation", comment: null },
  { uri: FINDING, label: "Finding", comment: null },
  { uri: INTERVENTION, label: "Intervention", comment: null },
  { uri: OUTCOME, label: "Outcome", comment: null },
  { uri: CONTEXT, label: "Context", comment: null },
  { uri: FUNDER, label: "Funder", comment: null },
  { uri: IMPLEMENTER, label: "Implementer", comment: null },
];

const essaObjectProperties: OntologyProperty[] = [
  {
    uri: "http://example.org/hasFinding",
    label: "has finding",
    comment: null,
    domain: [INVESTIGATION],
    range: [FINDING],
    property_type: "object",
  },
  {
    uri: "http://example.org/partOfInvestigation",
    label: "part of investigation",
    comment: null,
    domain: [FINDING],
    range: [INVESTIGATION],
    property_type: "object",
  },
  {
    uri: "http://example.org/evaluates",
    label: "evaluates",
    comment: null,
    domain: [FINDING],
    range: [INTERVENTION],
    property_type: "object",
  },
  {
    uri: "http://example.org/hasOutcome",
    label: "has outcome",
    comment: null,
    domain: [FINDING],
    range: [OUTCOME],
    property_type: "object",
  },
  {
    uri: "http://example.org/hasContext",
    label: "has context",
    comment: null,
    domain: [FINDING],
    range: [CONTEXT],
    property_type: "object",
  },
  {
    uri: "http://example.org/fundedBy",
    label: "funded by",
    comment: null,
    domain: [INVESTIGATION, INTERVENTION], // union domain (Fundable)
    range: [FUNDER],
    property_type: "object",
  },
  {
    uri: "http://example.org/implementedBy",
    label: "implemented by",
    comment: null,
    domain: [INTERVENTION],
    range: [IMPLEMENTER],
    property_type: "object",
  },
];

const mockOntology: CoreOntology = {
  classes: essaClasses,
  object_properties: essaObjectProperties,
  datatype_properties: [],
};

function makeProperty(overrides: Partial<Property> & Pick<Property, "id" | "domain_class">): Property {
  return {
    project_id: "proj-1",
    identifier: "prop",
    label: overrides.label ?? "Property",
    description: overrides.description ?? null,
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: null,
    cardinality: "single",
    required: false,
    uri: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    ...overrides,
  };
}

const mockSchemes: ConceptScheme[] = [
  {
    id: "scheme-1",
    project_id: "proj-1",
    title: "Countries",
    description: null,
    uri: "http://example.org/countries",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "scheme-2",
    project_id: "proj-1",
    title: "Topics",
    description: null,
    uri: "http://example.org/topics",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
];

// ============================================================
// Stripe 1: Helper Functions
// ============================================================

describe("extractStructuralEdges", () => {
  const knownClassUris = new Set(essaClasses.map((c) => c.uri));

  it("returns deduplicated edges for inverse property pairs", () => {
    const edges = extractStructuralEdges(essaObjectProperties, knownClassUris);
    // hasFinding and partOfInvestigation are inverses — should produce one edge
    const investigationFinding = edges.filter(
      (e) =>
        (e.sourceUri === INVESTIGATION && e.targetUri === FINDING) ||
        (e.sourceUri === FINDING && e.targetUri === INVESTIGATION)
    );
    expect(investigationFinding).toHaveLength(1);
  });

  it("keeps the forward direction for deduplicated inverses", () => {
    const edges = extractStructuralEdges(essaObjectProperties, knownClassUris);
    const edge = edges.find(
      (e) => e.sourceUri === INVESTIGATION && e.targetUri === FINDING
    );
    expect(edge).toBeDefined();
    expect(edge!.label).toBe("has finding");
  });

  it("expands union domains into multiple edges", () => {
    const edges = extractStructuralEdges(essaObjectProperties, knownClassUris);
    const fundedByEdges = edges.filter((e) => e.label === "funded by");
    expect(fundedByEdges).toHaveLength(2);
    const sources = fundedByEdges.map((e) => e.sourceUri).sort();
    expect(sources).toEqual([INTERVENTION, INVESTIGATION]);
  });

  it("excludes edges where domain or range is not a known class", () => {
    const unknownRangeProp: OntologyProperty = {
      uri: "http://example.org/linksTo",
      label: "links to",
      comment: null,
      domain: [FINDING],
      range: ["http://example.org/Unknown"],
      property_type: "object",
    };
    const edges = extractStructuralEdges(
      [...essaObjectProperties, unknownRangeProp],
      knownClassUris
    );
    const linksTo = edges.filter((e) => e.label === "links to");
    expect(linksTo).toHaveLength(0);
  });

  it("returns empty array when no object properties exist", () => {
    const edges = extractStructuralEdges([], knownClassUris);
    expect(edges).toEqual([]);
  });

  it("each edge has a unique id", () => {
    const edges = extractStructuralEdges(essaObjectProperties, knownClassUris);
    const ids = edges.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe("findHubClass", () => {
  const knownClassUris = new Set(essaClasses.map((c) => c.uri));

  it("returns Finding URI when Finding class exists", () => {
    const edges = extractStructuralEdges(essaObjectProperties, knownClassUris);
    const hub = findHubClass(essaClasses, edges);
    expect(hub).toBe(FINDING);
  });

  it("returns most-connected class when Finding is absent", () => {
    const classesNoFinding = essaClasses.filter((c) => c.uri !== FINDING);
    // Without Finding, edges that had Finding as source/target are gone
    const knownUris = new Set(classesNoFinding.map((c) => c.uri));
    const edges = extractStructuralEdges(essaObjectProperties, knownUris);
    const hub = findHubClass(classesNoFinding, edges);
    // Should pick whichever has the most connections
    expect(hub).toBeDefined();
    expect(hub).not.toBe(FINDING);
  });

  it("returns null when there are no classes", () => {
    const hub = findHubClass([], []);
    expect(hub).toBeNull();
  });
});

describe("findHubEdge", () => {
  const knownClassUris = new Set(essaClasses.map((c) => c.uri));

  it("finds the structural edge between selected and hub", () => {
    const edges = extractStructuralEdges(essaObjectProperties, knownClassUris);
    const result = findHubEdge(INVESTIGATION, FINDING, edges);
    expect(result).toBeDefined();
    expect(result!.label).toBe("has finding");
  });

  it("finds edge regardless of direction", () => {
    const edges = extractStructuralEdges(essaObjectProperties, knownClassUris);
    // Intervention → Finding via "evaluates" (Finding evaluates Intervention, source=Finding, target=Intervention)
    const result = findHubEdge(INTERVENTION, FINDING, edges);
    expect(result).toBeDefined();
    expect(result!.label).toBe("evaluates");
  });

  it("returns null when no edge connects selected and hub", () => {
    const edges = extractStructuralEdges(essaObjectProperties, knownClassUris);
    // Funder has no direct edge to Finding
    const result = findHubEdge(FUNDER, FINDING, edges);
    expect(result).toBeNull();
  });
});

// ============================================================
// Stripe 2: Layout (buildCarouselLayout + carouselGraphData)
// ============================================================

describe("buildCarouselLayout", () => {
  it("assigns 'selected' zone to the chosen class", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    const node = layout.nodes.find((n) => n.id === INVESTIGATION);
    expect(node).toBeDefined();
    expect(node!.zone).toBe("selected");
  });

  it("assigns 'hub' zone to Finding when another class is selected", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    const node = layout.nodes.find((n) => n.id === FINDING);
    expect(node).toBeDefined();
    expect(node!.zone).toBe("hub");
  });

  it("assigns 'spoke' zone to classes connected to hub", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    // Finding is hub. Intervention is connected to Finding via "evaluates"
    const intervention = layout.nodes.find((n) => n.id === INTERVENTION);
    expect(intervention).toBeDefined();
    expect(intervention!.zone).toBe("spoke");
  });

  it("assigns 'disconnected' zone to classes not connected to hub", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    // Funder and Implementer have no direct edge to Finding
    const funder = layout.nodes.find((n) => n.id === FUNDER);
    expect(funder).toBeDefined();
    expect(funder!.zone).toBe("disconnected");
  });

  it("when Finding is selected, it gets 'selected' zone with no separate hub", () => {
    const layout = buildCarouselLayout(
      FINDING,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    const finding = layout.nodes.find((n) => n.id === FINDING);
    expect(finding!.zone).toBe("selected");
    // No hub node
    const hubNodes = layout.nodes.filter((n) => n.zone === "hub");
    expect(hubNodes).toHaveLength(0);
    // Classes connected to Finding become spokes
    const investigation = layout.nodes.find((n) => n.id === INVESTIGATION);
    expect(investigation!.zone).toBe("spoke");
  });

  it("creates fan nodes for scheme-targeted properties of the selected class", () => {
    const projectProperties = [
      makeProperty({
        id: "p1",
        label: "country",
        domain_class: INVESTIGATION,
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
      }),
    ];

    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      projectProperties,
      mockSchemes
    );
    const fanNodes = layout.nodes.filter((n) => n.zone === "fan");
    expect(fanNodes).toHaveLength(1);
    expect(fanNodes[0].label).toBe("Countries");
    expect(fanNodes[0].type).toBe("scheme");
    expect(fanNodes[0].shape).toBe("hexagon");
  });

  it("creates property edges for fan connections", () => {
    const projectProperties = [
      makeProperty({
        id: "p1",
        label: "country",
        domain_class: INVESTIGATION,
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
      }),
    ];

    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      projectProperties,
      mockSchemes
    );
    const fanEdges = layout.edges.filter((e) => e.kind === "property");
    expect(fanEdges).toHaveLength(1);
    expect(fanEdges[0].label).toBe("country");
    expect(fanEdges[0].sourceId).toBe(INVESTIGATION);
    expect(fanEdges[0].targetId).toBe("scheme-1");
  });

  it("creates structural edge between selected and hub", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    const structuralEdges = layout.edges.filter((e) => e.kind === "structural");
    expect(structuralEdges.length).toBeGreaterThanOrEqual(1);
    const hubEdge = structuralEdges.find(
      (e) =>
        (e.sourceId === INVESTIGATION && e.targetId === FINDING) ||
        (e.sourceId === FINDING && e.targetId === INVESTIGATION)
    );
    expect(hubEdge).toBeDefined();
  });

  it("creates spoke edges between hub and spoke classes", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    const spokeEdges = layout.edges.filter((e) => e.kind === "spoke");
    expect(spokeEdges.length).toBeGreaterThan(0);
    // Each spoke edge connects hub to a spoke node
    for (const e of spokeEdges) {
      const isHubEdge =
        e.sourceId === FINDING || e.targetId === FINDING;
      expect(isHubEdge).toBe(true);
    }
  });

  it("no structural edge for disconnected class selected", () => {
    const layout = buildCarouselLayout(
      FUNDER,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    const structuralEdges = layout.edges.filter((e) => e.kind === "structural");
    // Funder is disconnected from Finding — no structural edge
    expect(structuralEdges).toHaveLength(0);
  });

  it("empty fan when selected class has no project properties", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      mockSchemes
    );
    const fanNodes = layout.nodes.filter((n) => n.zone === "fan");
    expect(fanNodes).toHaveLength(0);
  });

  it("all nodes have positions (x, y, width, height)", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    for (const node of layout.nodes) {
      expect(typeof node.x).toBe("number");
      expect(typeof node.y).toBe("number");
      expect(node.width).toBeGreaterThan(0);
      expect(node.height).toBeGreaterThan(0);
    }
  });

  it("selected node is positioned above hub", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    const selected = layout.nodes.find((n) => n.zone === "selected")!;
    const hub = layout.nodes.find((n) => n.zone === "hub")!;
    expect(selected.y).toBeLessThan(hub.y);
  });

  it("hub is positioned above spokes", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    const hub = layout.nodes.find((n) => n.zone === "hub")!;
    const spokes = layout.nodes.filter((n) => n.zone === "spoke");
    for (const spoke of spokes) {
      expect(hub.y).toBeLessThan(spoke.y);
    }
  });

  it("includes only class nodes for non-selected classes (no scheme nodes except fan)", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      mockSchemes
    );
    // No scheme nodes since no fan properties
    const schemeNodes = layout.nodes.filter((n) => n.type === "scheme");
    expect(schemeNodes).toHaveLength(0);
  });

  it("does not include the selected class as a spoke", () => {
    const layout = buildCarouselLayout(
      INVESTIGATION,
      essaClasses,
      essaObjectProperties,
      [],
      []
    );
    const spokeNodes = layout.nodes.filter((n) => n.zone === "spoke");
    expect(spokeNodes.find((n) => n.id === INVESTIGATION)).toBeUndefined();
  });
});

describe("carouselGraphData (signal)", () => {
  beforeEach(() => {
    ontology.value = null;
    properties.value = [];
    schemes.value = [];
    selectedClassUri.value = null;
  });

  it("returns null when ontology is not loaded", () => {
    selectedClassUri.value = INVESTIGATION;
    expect(carouselGraphData.value).toBeNull();
  });

  it("returns null when no class is selected", () => {
    ontology.value = mockOntology;
    expect(carouselGraphData.value).toBeNull();
  });

  it("returns layout data when ontology and selection are set", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const data = carouselGraphData.value;
    expect(data).not.toBeNull();
    expect(data!.nodes.length).toBeGreaterThan(0);
    expect(data!.width).toBeGreaterThan(0);
    expect(data!.height).toBeGreaterThan(0);
  });

  it("reacts to selectedClassUri changes", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const data1 = carouselGraphData.value!;
    const selected1 = data1.nodes.find((n) => n.zone === "selected")!;
    expect(selected1.id).toBe(INVESTIGATION);

    selectedClassUri.value = FINDING;
    const data2 = carouselGraphData.value!;
    const selected2 = data2.nodes.find((n) => n.zone === "selected")!;
    expect(selected2.id).toBe(FINDING);
  });

  it("includes fan nodes from project properties", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    properties.value = [
      makeProperty({
        id: "p1",
        label: "country",
        domain_class: INVESTIGATION,
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
      }),
    ];
    selectedClassUri.value = INVESTIGATION;

    const data = carouselGraphData.value!;
    const fanNodes = data.nodes.filter((n) => n.zone === "fan");
    expect(fanNodes).toHaveLength(1);
  });
});
