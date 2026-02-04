import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/preact";
import { PropertyPane } from "../../../src/components/workspace/PropertyPane";
import { properties, selectedPropertyId } from "../../../src/state/properties";
import type { Property } from "../../../src/types/models";

// Mock PropertyDetail to simplify testing
vi.mock("../../../src/components/properties/PropertyDetail", () => ({
  PropertyDetail: ({ property, onClose }: { property: Property; onClose: () => void }) => (
    <div data-testid="property-detail">
      <span>{property.label}</span>
      <button onClick={onClose}>Close</button>
    </div>
  ),
}));

const mockProperty: Property = {
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
};

describe("PropertyPane", () => {
  const mockOnDelete = vi.fn();
  const mockOnRefresh = vi.fn();
  const mockOnSchemeNavigate = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    properties.value = [mockProperty];
    selectedPropertyId.value = null;
  });

  it("shows empty state when no property selected", () => {
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
});
