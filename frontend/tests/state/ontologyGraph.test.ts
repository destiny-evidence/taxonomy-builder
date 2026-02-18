import { describe, it, expect, beforeEach } from "vitest";
import { ontology } from "../../src/state/ontology";
import { properties } from "../../src/state/properties";
import { schemes } from "../../src/state/schemes";
import { ontologyGraphData } from "../../src/state/ontologyGraph";
import type { CoreOntology, Property, ConceptScheme } from "../../src/types/models";

const mockOntology: CoreOntology = {
  classes: [
    { uri: "http://example.org/Investigation", label: "Investigation", comment: "A research effort" },
    { uri: "http://example.org/Finding", label: "Finding", comment: "A specific result" },
    { uri: "http://example.org/Intervention", label: "Intervention", comment: null },
  ],
  object_properties: [],
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
    description: "A list of countries",
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
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("ontologyGraphData", () => {
  beforeEach(() => {
    ontology.value = null;
    properties.value = [];
    schemes.value = [];
  });

  it("returns null when ontology is not loaded", () => {
    expect(ontologyGraphData.value).toBeNull();
  });

  it("returns class nodes from ontology classes", () => {
    ontology.value = mockOntology;
    const data = ontologyGraphData.value!;
    const classNodes = data.nodes.filter((n) => n.type === "class");
    expect(classNodes).toHaveLength(3);
    expect(classNodes.map((n) => n.label).sort()).toEqual(["Finding", "Intervention", "Investigation"]);
  });

  it("returns scheme nodes from schemes signal", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    const data = ontologyGraphData.value!;
    const schemeNodes = data.nodes.filter((n) => n.type === "scheme");
    expect(schemeNodes).toHaveLength(2);
    expect(schemeNodes.map((n) => n.label).sort()).toEqual(["Countries", "Topics"]);
  });

  it("returns edges from properties with range_scheme_id", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    properties.value = [
      makeProperty({
        id: "p1",
        label: "country",
        domain_class: "http://example.org/Investigation",
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
      }),
    ];

    const data = ontologyGraphData.value!;
    expect(data.edges).toHaveLength(1);
    expect(data.edges[0].label).toBe("country");
    expect(data.edges[0].sourceId).toBe("http://example.org/Investigation");
    expect(data.edges[0].targetId).toBe("scheme-1");
  });

  it("returns datatype edges for properties with range_datatype", () => {
    ontology.value = mockOntology;
    properties.value = [
      makeProperty({
        id: "p2",
        label: "birthDate",
        domain_class: "http://example.org/Finding",
        range_datatype: "xsd:date",
      }),
    ];

    const data = ontologyGraphData.value!;
    expect(data.edges).toHaveLength(1);
    expect(data.edges[0].label).toBe("birthDate");
    expect(data.edges[0].targetId).toBe("xsd:date");
  });

  it("only includes datatypes that are referenced by properties", () => {
    ontology.value = mockOntology;
    properties.value = [
      makeProperty({
        id: "p2",
        label: "birthDate",
        domain_class: "http://example.org/Finding",
        range_datatype: "xsd:date",
      }),
    ];

    const data = ontologyGraphData.value!;
    const datatypeNodes = data.nodes.filter((n) => n.type === "datatype");
    expect(datatypeNodes).toHaveLength(1);
    expect(datatypeNodes[0].label).toBe("Date");
  });

  it("marks connected nodes and dims orphans", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    properties.value = [
      makeProperty({
        id: "p1",
        label: "country",
        domain_class: "http://example.org/Investigation",
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
      }),
    ];

    const data = ontologyGraphData.value!;
    const investigationNode = data.nodes.find((n) => n.id === "http://example.org/Investigation");
    const findingNode = data.nodes.find((n) => n.id === "http://example.org/Finding");
    const countriesNode = data.nodes.find((n) => n.id === "scheme-1");
    const topicsNode = data.nodes.find((n) => n.id === "scheme-2");

    expect(investigationNode!.connected).toBe(true);
    expect(findingNode!.connected).toBe(false);
    expect(countriesNode!.connected).toBe(true);
    expect(topicsNode!.connected).toBe(false);
  });

  it("handles empty state — no properties means all nodes dimmed", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    properties.value = [];

    const data = ontologyGraphData.value!;
    expect(data.edges).toHaveLength(0);
    expect(data.nodes.every((n) => !n.connected)).toBe(true);
  });

  it("creates synthetic class node for unknown domain_class URI", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    properties.value = [
      makeProperty({
        id: "p1",
        label: "foo",
        domain_class: "http://example.org/Unknown",
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
      }),
    ];

    const data = ontologyGraphData.value!;
    const syntheticNode = data.nodes.find((n) => n.id === "http://example.org/Unknown");
    expect(syntheticNode).toBeDefined();
    expect(syntheticNode!.label).toBe("http://example.org/Unknown");
    expect(syntheticNode!.type).toBe("class");
    expect(syntheticNode!.connected).toBe(true);
  });

  it("detects parallel edges between same endpoints", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    properties.value = [
      makeProperty({
        id: "p1",
        label: "country",
        domain_class: "http://example.org/Investigation",
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
      }),
      makeProperty({
        id: "p2",
        label: "origin",
        domain_class: "http://example.org/Investigation",
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
      }),
    ];

    const data = ontologyGraphData.value!;
    expect(data.edges).toHaveLength(2);
    const offsets = data.edges.map((e) => e.parallelOffset);
    // Parallel edges should be offset symmetrically around 0
    expect(offsets).not.toEqual([0, 0]);
    expect(offsets[0]).toBe(-offsets[1]);
  });

  it("places class nodes in left column and scheme/datatype nodes in right column", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;

    const data = ontologyGraphData.value!;
    const classNodes = data.nodes.filter((n) => n.type === "class");
    const schemeNodes = data.nodes.filter((n) => n.type === "scheme");

    const classXs = new Set(classNodes.map((n) => n.x));
    expect(classXs.size).toBe(1);

    const schemeXs = new Set(schemeNodes.map((n) => n.x));
    expect(schemeXs.size).toBe(1);

    expect([...classXs][0]).toBeLessThan([...schemeXs][0]);
  });

  it("preserves backend order for left column class nodes", () => {
    ontology.value = mockOntology;

    const data = ontologyGraphData.value!;
    const classNodes = data.nodes.filter((n) => n.type === "class");
    const labels = classNodes.map((n) => n.label);
    // Backend order from mockOntology.classes, matching ProjectPane
    expect(labels).toEqual(["Investigation", "Finding", "Intervention"]);
  });

  it("includes property metadata on edges", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    properties.value = [
      makeProperty({
        id: "p1",
        label: "country",
        description: "The country of origin",
        domain_class: "http://example.org/Investigation",
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
        required: true,
        cardinality: "multiple",
      }),
    ];

    const data = ontologyGraphData.value!;
    const edge = data.edges[0];
    expect(edge.description).toBe("The country of origin");
    expect(edge.required).toBe(true);
    expect(edge.cardinality).toBe("multiple");
  });
});
