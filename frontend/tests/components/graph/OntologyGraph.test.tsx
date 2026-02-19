import { describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/preact";
import { ontology, selectedClassUri } from "../../../src/state/ontology";
import { properties } from "../../../src/state/properties";
import { schemes } from "../../../src/state/schemes";
import { OntologyGraph } from "../../../src/components/graph/OntologyGraph";
import type { CoreOntology, OntologyProperty } from "../../../src/types/models";

const INVESTIGATION = "http://example.org/Investigation";
const FINDING = "http://example.org/Finding";
const INTERVENTION = "http://example.org/Intervention";
const OUTCOME = "http://example.org/Outcome";

const essaClasses = [
  { uri: INVESTIGATION, label: "Investigation", comment: "A research effort" },
  { uri: FINDING, label: "Finding", comment: "A specific result" },
  { uri: INTERVENTION, label: "Intervention", comment: null },
  { uri: OUTCOME, label: "Outcome", comment: null },
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
];

const mockOntology: CoreOntology = {
  classes: essaClasses,
  object_properties: essaObjectProperties,
  datatype_properties: [],
};

describe("OntologyGraph component", () => {
  beforeEach(() => {
    ontology.value = null;
    properties.value = [];
    schemes.value = [];
    selectedClassUri.value = null;
  });

  it("shows empty message when no ontology is loaded", () => {
    const { container } = render(<OntologyGraph />);
    expect(container.textContent).toContain("No core ontology loaded");
  });

  it("shows select-class message when no class is selected", () => {
    ontology.value = mockOntology;
    const { container } = render(<OntologyGraph />);
    expect(container.textContent).toContain("Select a class to view");
  });

  it("renders SVG when ontology and class are selected", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const { container } = render(<OntologyGraph />);
    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
  });

  it("renders class nodes as SVG groups with data-node-type", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const { container } = render(<OntologyGraph />);
    const classNodes = container.querySelectorAll("[data-node-type='class']");
    expect(classNodes.length).toBeGreaterThan(0);
  });

  it("renders the selected class with data-zone=selected", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const { container } = render(<OntologyGraph />);
    const selectedNode = container.querySelector("[data-zone='selected']");
    expect(selectedNode).toBeTruthy();
    expect(selectedNode!.textContent).toContain("Investigation");
  });

  it("renders hub node with data-zone=hub", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const { container } = render(<OntologyGraph />);
    const hubNode = container.querySelector("[data-zone='hub']");
    expect(hubNode).toBeTruthy();
    expect(hubNode!.textContent).toContain("Finding");
  });

  it("renders spoke nodes", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const { container } = render(<OntologyGraph />);
    const spokeNodes = container.querySelectorAll("[data-zone='spoke']");
    expect(spokeNodes.length).toBeGreaterThan(0);
  });

  it("clicking a class node updates selectedClassUri", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const { container } = render(<OntologyGraph />);
    const hubNode = container.querySelector("[data-zone='hub']");
    expect(hubNode).toBeTruthy();
    hubNode!.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(selectedClassUri.value).toBe(FINDING);
  });

  it("renders edges with data-edge-kind attribute", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const { container } = render(<OntologyGraph />);
    const edges = container.querySelectorAll("[data-edge-kind]");
    expect(edges.length).toBeGreaterThan(0);
  });

  it("renders hexagon shapes for fan scheme nodes", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    schemes.value = [
      {
        id: "scheme-1",
        project_id: "proj-1",
        title: "Countries",
        description: null,
        uri: "http://example.org/countries",
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
    ];
    properties.value = [
      {
        id: "p1",
        project_id: "proj-1",
        identifier: "country",
        label: "country",
        description: null,
        domain_class: INVESTIGATION,
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: null },
        range_datatype: null,
        cardinality: "single",
        required: false,
        uri: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
    ];

    const { container } = render(<OntologyGraph />);
    const hexagons = container.querySelectorAll("[data-shape='hexagon']");
    expect(hexagons.length).toBe(1);
  });

  it("renders node titles for tooltips", () => {
    ontology.value = mockOntology;
    selectedClassUri.value = INVESTIGATION;
    const { container } = render(<OntologyGraph />);
    const selectedNode = container.querySelector("[data-zone='selected']");
    const title = selectedNode!.querySelector("title");
    expect(title!.textContent).toContain("Investigation");
    expect(title!.textContent).toContain("A research effort");
  });
});
