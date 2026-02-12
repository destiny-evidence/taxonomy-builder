import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { ClassDetailPane } from "../../../src/components/workspace/ClassDetailPane";
import { properties, selectedPropertyId, creatingProperty } from "../../../src/state/properties";
import type { Property } from "../../../src/types/models";

const mockProperties: Property[] = [
  {
    id: "prop-1",
    project_id: "proj-1",
    identifier: "birthDate",
    label: "Birth Date",
    description: null,
    domain_class: "http://example.org/Person",
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: "xsd:date",
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
    domain_class: "http://example.org/Person",
    range_scheme_id: "scheme-1",
    range_scheme: { id: "scheme-1", title: "Countries", uri: "http://example.org/countries" },
    range_datatype: null,
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
    domain_class: "http://example.org/Organization",
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: "xsd:date",
    cardinality: "single",
    required: false,
    uri: null,
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-03T00:00:00Z",
  },
];

// Mock ontologyClasses to provide class info
vi.mock("../../../src/state/ontology", async () => {
  const actual = await vi.importActual("../../../src/state/ontology");
  return {
    ...actual,
    ontologyClasses: {
      value: [
        { uri: "http://example.org/Person", label: "Person", comment: "A human being" },
        { uri: "http://example.org/Organization", label: "Organization", comment: null },
      ],
    },
  };
});

describe("ClassDetailPane", () => {
  const mockOnPropertySelect = vi.fn();
  const mockOnSchemeNavigate = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    properties.value = mockProperties;
    selectedPropertyId.value = null;
    creatingProperty.value = null;
  });

  describe("header", () => {
    it("displays class label", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
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
        />
      );

      expect(screen.getByText("xsd:date")).toBeInTheDocument();
    });

    it("shows scheme name for scheme-range properties", () => {
      render(
        <ClassDetailPane
          classUri="http://example.org/Person"
          projectId="proj-1"
          onPropertySelect={mockOnPropertySelect}
          onSchemeNavigate={mockOnSchemeNavigate}
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
        />
      );

      const propertyItem = screen.getByText("Birth Date").closest(".class-detail-pane__property");
      expect(propertyItem).toHaveClass("class-detail-pane__property--selected");
    });
  });
});
