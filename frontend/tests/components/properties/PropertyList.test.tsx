import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { PropertyList } from "../../../src/components/properties/PropertyList";
import { properties, propertiesLoading, propertiesError } from "../../../src/state/properties";
import type { Property } from "../../../src/types/models";

const mockProperties: Property[] = [
  {
    id: "prop-1",
    project_id: "proj-1",
    identifier: "birthDate",
    label: "Birth Date",
    description: "Date of birth",
    domain_class: "http://example.org/Person",
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: "xsd:date",
    cardinality: "single",
    required: false,
    uri: "http://example.org/birthDate",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "prop-2",
    project_id: "proj-1",
    identifier: "nationality",
    label: "Nationality",
    description: "Country of citizenship",
    domain_class: "http://example.org/Person",
    range_scheme_id: "scheme-1",
    range_scheme: { id: "scheme-1", title: "Countries", uri: "http://example.org/countries" },
    range_datatype: null,
    cardinality: "multiple",
    required: true,
    uri: "http://example.org/nationality",
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("PropertyList", () => {
  const mockOnSelect = vi.fn();
  const mockOnNew = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    properties.value = mockProperties;
    propertiesLoading.value = false;
    propertiesError.value = null;
  });

  it("renders property labels", () => {
    render(<PropertyList onSelect={mockOnSelect} onNew={mockOnNew} />);

    expect(screen.getByText("Birth Date")).toBeInTheDocument();
    expect(screen.getByText("Nationality")).toBeInTheDocument();
  });

  it("shows range datatype for datatype properties", () => {
    render(<PropertyList onSelect={mockOnSelect} onNew={mockOnNew} />);

    expect(screen.getByText("xsd:date")).toBeInTheDocument();
  });

  it("shows range scheme title for scheme properties", () => {
    render(<PropertyList onSelect={mockOnSelect} onNew={mockOnNew} />);

    expect(screen.getByText("Countries")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    propertiesLoading.value = true;

    render(<PropertyList onSelect={mockOnSelect} onNew={mockOnNew} />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    propertiesError.value = "Failed to load properties";

    render(<PropertyList onSelect={mockOnSelect} onNew={mockOnNew} />);

    expect(screen.getByText("Failed to load properties")).toBeInTheDocument();
  });

  it("shows empty state when no properties", () => {
    properties.value = [];

    render(<PropertyList onSelect={mockOnSelect} onNew={mockOnNew} />);

    expect(screen.getByText(/no properties/i)).toBeInTheDocument();
  });

  it("calls onSelect when property is clicked", () => {
    render(<PropertyList onSelect={mockOnSelect} onNew={mockOnNew} />);

    fireEvent.click(screen.getByText("Birth Date"));

    expect(mockOnSelect).toHaveBeenCalledWith("prop-1");
  });

  it("calls onNew when New Property button is clicked", () => {
    render(<PropertyList onSelect={mockOnSelect} onNew={mockOnNew} />);

    fireEvent.click(screen.getByText("+ New Property"));

    expect(mockOnNew).toHaveBeenCalled();
  });

  it("shows required indicator for required properties", () => {
    render(<PropertyList onSelect={mockOnSelect} onNew={mockOnNew} />);

    // Nationality is required
    const nationalityRow = screen.getByText("Nationality").closest(".property-list__item");
    expect(nationalityRow).toHaveTextContent("required");
  });
});
