import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/preact";
import { PropertyPane } from "../../../src/components/workspace/PropertyPane";
import { properties, selectedPropertyId, creatingProperty } from "../../../src/state/properties";
import { currentProject } from "../../../src/state/projects";
import type { Property } from "../../../src/types/models";

// Mock PropertyDetail to simplify testing
vi.mock("../../../src/components/properties/PropertyDetail", () => ({
  PropertyDetail: (props: Record<string, unknown>) => {
    if (props.mode === "create") {
      return (
        <div data-testid="property-detail-create">
          <span>Create mode</span>
          <span>projectId: {props.projectId as string}</span>
        </div>
      );
    }
    const property = props.property as Property;
    return (
      <div data-testid="property-detail">
        <span>{property.label}</span>
        <button onClick={props.onClose as () => void}>Close</button>
      </div>
    );
  },
}));

const mockProperty: Property = {
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
};

describe("PropertyPane", () => {
  const mockOnDelete = vi.fn();
  const mockOnRefresh = vi.fn();
  const mockOnSchemeNavigate = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    properties.value = [mockProperty];
    selectedPropertyId.value = null;
    creatingProperty.value = null;
  });

  it("shows empty state when no property selected and not creating", () => {
    render(
      <PropertyPane
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
        onSchemeNavigate={mockOnSchemeNavigate}
      />
    );

    expect(screen.getByText(/select a property/i)).toBeInTheDocument();
  });

  it("shows PropertyDetail when property is selected", () => {
    selectedPropertyId.value = "prop-1";

    render(
      <PropertyPane
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
        onSchemeNavigate={mockOnSchemeNavigate}
      />
    );

    expect(screen.getByTestId("property-detail")).toBeInTheDocument();
    expect(screen.getByText("Birth Date")).toBeInTheDocument();
  });

  it("clears selection when close is called", () => {
    selectedPropertyId.value = "prop-1";

    render(
      <PropertyPane
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
        onSchemeNavigate={mockOnSchemeNavigate}
      />
    );

    screen.getByText("Close").click();

    expect(selectedPropertyId.value).toBe(null);
  });

  it("shows create mode when creatingProperty is set", () => {
    creatingProperty.value = { projectId: "proj-1", domainClassUri: "http://example.org/Person" };

    render(
      <PropertyPane
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
        onSchemeNavigate={mockOnSchemeNavigate}
      />
    );

    expect(screen.getByTestId("property-detail-create")).toBeInTheDocument();
    expect(screen.getByText("Create mode")).toBeInTheDocument();
  });

  it("prioritizes create mode over selected property", () => {
    selectedPropertyId.value = "prop-1";
    creatingProperty.value = { projectId: "proj-1" };

    render(
      <PropertyPane
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
        onSchemeNavigate={mockOnSchemeNavigate}
      />
    );

    expect(screen.getByTestId("property-detail-create")).toBeInTheDocument();
    expect(screen.queryByTestId("property-detail")).not.toBeInTheDocument();
  });

  it("hides values section during create mode", () => {
    creatingProperty.value = { projectId: "proj-1" };

    render(
      <PropertyPane
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
        onSchemeNavigate={mockOnSchemeNavigate}
      />
    );

    expect(document.querySelector(".property-pane__values")).not.toBeInTheDocument();
  });

  describe("property without a range", () => {
    beforeEach(() => {
      currentProject.value = {
        id: "proj-1",
        name: "Example",
        description: null,
        namespace: "http://example.org/",
        namespace_prefixes: {},
        identifier_prefix: "EX",
        identifier_counter: 0,
        prefix_locked: false,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      };
      selectedPropertyId.value = "prop-1";
    });

    afterEach(() => {
      currentProject.value = null;
    });

    function renderPane() {
      render(
        <PropertyPane
          onDelete={mockOnDelete}
          onRefresh={mockOnRefresh}
          onSchemeNavigate={mockOnSchemeNavigate}
        />
      );
    }

    it("shows no-range label for an external property", () => {
      properties.value = [
        { ...mockProperty, range_datatype: null, uri: "http://www.w3.org/2003/01/geo/wgs84_pos#lat" },
      ];
      renderPane();

      expect(document.querySelector(".property-pane__values")).toHaveTextContent(
        "Any (no range declared)"
      );
    });

    it("shows no-range label for an in-namespace rdf:Property", () => {
      properties.value = [
        { ...mockProperty, range_datatype: null, property_type: "rdf", uri: "http://example.org/birthDate" },
      ];
      renderPane();

      expect(document.querySelector(".property-pane__values")).toHaveTextContent(
        "Any (no range declared)"
      );
    });

    it("shows missing-range label for an in-namespace datatype property", () => {
      properties.value = [
        { ...mockProperty, range_datatype: null, uri: "http://example.org/birthDate" },
      ];
      renderPane();

      expect(document.querySelector(".property-pane__datatype--missing")).toHaveTextContent(
        "No range set"
      );
    });
  });
});
