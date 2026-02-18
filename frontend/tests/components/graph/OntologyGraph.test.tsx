import { describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/preact";
import { OntologyGraph } from "../../../src/components/graph/OntologyGraph";
import { ontology } from "../../../src/state/ontology";
import { properties } from "../../../src/state/properties";
import { schemes } from "../../../src/state/schemes";
import type { CoreOntology, Property, ConceptScheme } from "../../../src/types/models";

const mockOntology: CoreOntology = {
  classes: [
    { uri: "http://example.org/Investigation", label: "Investigation", comment: "A research effort" },
    { uri: "http://example.org/Finding", label: "Finding", comment: "A specific result" },
  ],
  object_properties: [],
  datatype_properties: [],
};

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
];

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

describe("OntologyGraph", () => {
  beforeEach(() => {
    ontology.value = null;
    properties.value = [];
    schemes.value = [];
  });

  it("shows no-ontology message when ontology is null", () => {
    const { container } = render(<OntologyGraph />);
    expect(container.textContent).toContain("No core ontology loaded");
  });

  it("renders correct number of class nodes", () => {
    ontology.value = mockOntology;
    const { container } = render(<OntologyGraph />);
    const classNodes = container.querySelectorAll("[data-node-type='class']");
    expect(classNodes).toHaveLength(2);
  });

  it("renders correct number of scheme nodes", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    const { container } = render(<OntologyGraph />);
    const schemeNodes = container.querySelectorAll("[data-node-type='scheme']");
    expect(schemeNodes).toHaveLength(1);
  });

  it("renders datatype badges only when referenced by properties", () => {
    ontology.value = mockOntology;
    properties.value = [
      makeProperty({
        id: "p1",
        label: "birthDate",
        domain_class: "http://example.org/Finding",
        range_datatype: "xsd:date",
      }),
    ];

    const { container } = render(<OntologyGraph />);
    const datatypeNodes = container.querySelectorAll("[data-node-type='datatype']");
    expect(datatypeNodes).toHaveLength(1);
    expect(datatypeNodes[0].textContent).toContain("Date");
  });

  it("does not render datatype nodes when no properties reference them", () => {
    ontology.value = mockOntology;
    const { container } = render(<OntologyGraph />);
    const datatypeNodes = container.querySelectorAll("[data-node-type='datatype']");
    expect(datatypeNodes).toHaveLength(0);
  });

  it("applies dimmed class to orphan nodes", () => {
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

    const { container } = render(<OntologyGraph />);
    const findingNode = container.querySelector("[data-node-id='http://example.org/Finding']");
    expect(findingNode!.classList.contains("ontology-graph__node--dimmed")).toBe(true);

    const investigationNode = container.querySelector("[data-node-id='http://example.org/Investigation']");
    expect(investigationNode!.classList.contains("ontology-graph__node--dimmed")).toBe(false);
  });

  it("renders edge labels with correct text", () => {
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

    const { container } = render(<OntologyGraph />);
    const edgeLabels = container.querySelectorAll("[data-edge-label]");
    expect(edgeLabels).toHaveLength(1);
    expect(edgeLabels[0].textContent).toContain("country");
  });

  it("renders SVG container when ontology is loaded", () => {
    ontology.value = mockOntology;
    const { container } = render(<OntologyGraph />);
    const svg = container.querySelector(".ontology-graph__svg");
    expect(svg).not.toBeNull();
  });

  it("renders SVG title tooltips for class nodes", () => {
    ontology.value = mockOntology;
    const { container } = render(<OntologyGraph />);
    const investigationNode = container.querySelector("[data-node-id='http://example.org/Investigation']");
    const title = investigationNode!.querySelector("title");
    expect(title!.textContent).toContain("Investigation");
    expect(title!.textContent).toContain("A research effort");
  });

  it("renders edge group with label chip for edges", () => {
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

    const { container } = render(<OntologyGraph />);
    const edgeGroup = container.querySelector("[data-edge-id='p1']");
    expect(edgeGroup).not.toBeNull();
    const labelChip = edgeGroup!.querySelector("[data-edge-label]");
    expect(labelChip!.textContent).toContain("country");
  });

  it("renders all nodes dimmed when there are no edges", () => {
    ontology.value = mockOntology;
    schemes.value = mockSchemes;
    properties.value = [];

    const { container } = render(<OntologyGraph />);
    const allNodes = container.querySelectorAll("[data-node-type]");
    const dimmedNodes = container.querySelectorAll(".ontology-graph__node--dimmed");
    expect(dimmedNodes.length).toBe(allNodes.length);
  });
});
