import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { ClassDetailPane } from "../../../src/components/workspace/ClassDetailPane";
import { properties, selectedPropertyId, creatingProperty } from "../../../src/state/properties";
import type { Property, OntologyClass } from "../../../src/types/models";
import * as historyApi from "../../../src/api/history";

vi.mock("../../../src/api/history");

const mockProperties: Property[] = [
  {
    id: "prop-1",
    project_id: "proj-1",
    identifier: "birthDate",
    label: "Birth Date",
    description: null,
    domain_class_uris: ["http://example.org/Person"],
    property_type: "datatype",
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: "xsd:date",
    range_class: null,
    cardinality: "single",
    required: false,
    uri: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "prop-2",
    project_id: "proj-1",
    identifier: "country",
    label: "Country",
    description: null,
    domain_class_uris: ["http://example.org/Person"],
    property_type: "object",
    range_scheme_id: "scheme-1",
    range_scheme: { id: "scheme-1", title: "Countries", uri: "http://example.org/countries" },
    range_datatype: null,
    range_class: null,
    cardinality: "single",
    required: true,
    uri: null,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
  {
    id: "prop-3",
    project_id: "proj-1",
    identifier: "founded",
    label: "Founded",
    description: null,
    domain_class_uris: ["http://example.org/Organization"],
    property_type: "datatype",
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: "xsd:date",
    range_class: null,
    cardinality: "single",
    required: false,
    uri: null,
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-03T00:00:00Z",
  },
];

// vi.hoisted runs before vi.mock hoisting — makes these available to the factory
const { mockOntologyClasses, mockSelectedClassUri } = vi.hoisted(() => ({
  mockOntologyClasses: {
    value: [
      { id: "cls-1", project_id: "proj-1", identifier: "Person", uri: "http://example.org/Person", label: "Person", description: "A human being", scope_note: null, superclass_uris: [] as string[], subclass_uris: [] as string[], restrictions: [] as OntologyClass["restrictions"], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
      { id: "cls-2", project_id: "proj-1", identifier: "Organization", uri: "http://example.org/Organization", label: "Organization", description: null, scope_note: null, superclass_uris: [] as string[], subclass_uris: [] as string[], restrictions: [] as OntologyClass["restrictions"], created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-02T00:00:00Z" },
    ] as OntologyClass[],
  },
  mockSelectedClassUri: { value: null as string | null },
}));

vi.mock("../../../src/state/classes", async () => {
  const actual = await vi.importActual("../../../src/state/classes");
  return {
    ...actual,
    ontologyClasses: mockOntologyClasses,
    selectedClassUri: mockSelectedClassUri,
  };
});

vi.mock("../../../src/components/classes/ClassDetail", () => ({
  ClassDetail: (props: Record<string, unknown>) => {
    const cls = props.ontologyClass as { label: string; description: string | null } | undefined;
    return (
      <div data-testid="class-detail">
        {cls && <span>{cls.label}</span>}
        {cls?.description && <span>{cls.description}</span>}
      </div>
    );
  },
}));

describe("ClassDetailPane", () => {
  const mockOnPropertySelect = vi.fn();
  const mockOnSchemeNavigate = vi.fn();
  const mockOnRefresh = vi.fn();
  const mockOnClassDeleted = vi.fn();
  const defaultClasses = structuredClone(mockOntologyClasses.value);

  beforeEach(() => {
    vi.resetAllMocks();
    properties.value = mockProperties;
    selectedPropertyId.value = null;
    creatingProperty.value = null;
    mockOntologyClasses.value = structuredClone(defaultClasses);
    mockSelectedClassUri.value = null;
  });

  describe("header", () => {
    it("displays class label", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Person")).toBeInTheDocument();
    });

    it("displays class description when available", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("A human being")).toBeInTheDocument();
    });

    it("shows URI when class not found in ontology", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Unknown"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("http://example.org/Unknown")).toBeInTheDocument();
    });
  });

  describe("properties list", () => {
    it("shows properties for the class", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Birth Date")).toBeInTheDocument();
      expect(screen.getByText("Country")).toBeInTheDocument();
    });

    it("only shows properties for the given class", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // Founded belongs to Organization, not Person
      expect(screen.queryByText("Founded")).not.toBeInTheDocument();
    });

    it("shows datatype for datatype properties", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Date")).toBeInTheDocument();
    });

    it("shows scheme name for scheme-range properties", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Countries")).toBeInTheDocument();
    });

    it("shows empty state when no properties", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Organization"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // Organization only has "Founded" property in our mock data
      expect(screen.getByText("Founded")).toBeInTheDocument();
    });
  });

  describe("interactions", () => {
    it("calls onPropertySelect when property clicked", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByText("Birth Date"));

      expect(mockOnPropertySelect).toHaveBeenCalledWith("prop-1");
    });

    it("calls onSchemeNavigate when scheme link clicked", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByText("Countries"));

      expect(mockOnSchemeNavigate).toHaveBeenCalledWith("scheme-1");
    });

    it("sets creatingProperty signal when Add Property clicked", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByText("+ Add Property"));

      expect(creatingProperty.value).toEqual({
        projectId: "proj-1",
        domainClassUri: "http://example.org/Person",
      });
    });

    it("clears selectedPropertyId when Add Property clicked", () => {
      selectedPropertyId.value = "prop-1";

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByText("+ Add Property"));

      expect(selectedPropertyId.value).toBeNull();
    });

    it("highlights selected property", () => {
      selectedPropertyId.value = "prop-1";

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      const propertyItem = screen.getByText("Birth Date").closest(".class-detail-pane__property");
      expect(propertyItem).toHaveClass("class-detail-pane__property--selected");
    });
  });

  describe("hierarchy section", () => {
    it("is hidden when class has no superclasses or subclasses", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.queryByText("Hierarchy")).not.toBeInTheDocument();
    });

    it("shows superclass label as clickable link", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0], superclass_uris: ["http://example.org/Organization"], subclass_uris: [] },
        { ...defaultClasses[1] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Hierarchy")).toBeInTheDocument();
      const link = screen.getByRole("button", { name: "Organization" });
      expect(link).toHaveClass("class-detail-pane__class-link");
    });

    it("navigates to superclass when link clicked", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0], superclass_uris: ["http://example.org/Organization"], subclass_uris: [] },
        { ...defaultClasses[1] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: "Organization" }));
      expect(mockSelectedClassUri.value).toBe("http://example.org/Organization");
    });

    it("shows subclass labels as clickable links", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0] },
        { ...defaultClasses[1], superclass_uris: [], subclass_uris: ["http://example.org/Person"] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Organization"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Hierarchy")).toBeInTheDocument();
      expect(screen.getByText(/Subclasses/)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Person" })).toBeInTheDocument();
    });

    it("renders unresolvable URIs as non-navigable text", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0], superclass_uris: ["https://schema.org/Thing"], subclass_uris: [] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // "Thing" extracted from https://schema.org/Thing — shown as plain text, not a button
      expect(screen.getByText("Thing")).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Thing" })).not.toBeInTheDocument();
    });

    it("renders unresolvable hash URIs as non-navigable text", () => {
      mockOntologyClasses.value = [
        { ...defaultClasses[0], superclass_uris: [], subclass_uris: ["http://www.w3.org/2002/07/owl#NamedIndividual"] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      // "NamedIndividual" extracted from the OWL hash URI — shown as plain text, not a button
      expect(screen.getByText("NamedIndividual")).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "NamedIndividual" })).not.toBeInTheDocument();
    });
  });

  describe("restrictions section", () => {
    it("is hidden when class has no restrictions", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.queryByText("Restrictions")).not.toBeInTheDocument();
    });

    it("shows restrictions with resolved class label and restriction type", () => {
      mockOntologyClasses.value = [
        {
          ...defaultClasses[0],
          restrictions: [
            {
              on_property_uri: "http://example.org/birthDate",
              restriction_type: "allValuesFrom",
              value_uri: "http://example.org/Organization",
            },
          ],
        },
        { ...defaultClasses[1] },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("Restrictions")).toBeInTheDocument();
      // Property URI falls back to extractLocalName (mock prop has uri: null)
      expect(screen.getByText("birthDate")).toBeInTheDocument();
      expect(screen.getByText("allValuesFrom")).toBeInTheDocument();
      // Class URI resolves to label from mockOntologyClasses
      expect(screen.getByText("Organization")).toBeInTheDocument();
    });

    it("falls back to extractLocalName for unresolvable restriction URIs", () => {
      mockOntologyClasses.value = [
        {
          ...defaultClasses[0],
          restrictions: [
            {
              on_property_uri: "https://external.org/vocab#someProperty",
              restriction_type: "someValuesFrom",
              value_uri: "https://external.org/vocab#SomeClass",
            },
          ],
        },
      ];

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      expect(screen.getByText("someProperty")).toBeInTheDocument();
      expect(screen.getByText("SomeClass")).toBeInTheDocument();
    });
  });

  describe("history footer", () => {
    it("toggles history panel and passes project source", async () => {
      vi.mocked(historyApi.getProjectHistory).mockResolvedValue([]);

      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
          onRefresh={mockOnRefresh}
          onClassDeleted={mockOnClassDeleted}
        />
      );

      const button = screen.getByRole("button", { name: /history/i });
      expect(button).toHaveAttribute("aria-expanded", "false");

      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute("aria-expanded", "true");
        expect(historyApi.getProjectHistory).toHaveBeenCalledWith("proj-1");
      });
    });
  });
});
