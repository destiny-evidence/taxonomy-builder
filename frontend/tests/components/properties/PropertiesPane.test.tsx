import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { PropertiesPane } from "../../../src/components/properties/PropertiesPane";
import type { Property, ConceptScheme, OntologyClass } from "../../../src/types/models";

const mockSchemes: ConceptScheme[] = [
  {
    id: "scheme-1",
    project_id: "proj-1",
    title: "Animals",
    description: null,
    uri: "http://example.org/animals",
    publisher: null,
    version: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
];

const mockOntologyClasses: OntologyClass[] = [
  { uri: "http://example.org/Finding", label: "Finding", comment: null },
];

const mockProperties: Property[] = [
  {
    id: "prop-1",
    project_id: "proj-1",
    identifier: "has-author",
    label: "Has Author",
    description: "The author",
    domain_class: "http://example.org/Finding",
    range_scheme_id: "scheme-1",
    range_scheme: { id: "scheme-1", title: "Animals", uri: "http://example.org/animals" },
    range_datatype: null,
    cardinality: "single",
    required: true,
    uri: "http://example.org/has-author",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "prop-2",
    project_id: "proj-1",
    identifier: "publication-date",
    label: "Publication Date",
    description: null,
    domain_class: "http://example.org/Finding",
    range_scheme_id: null,
    range_scheme: null,
    range_datatype: "xsd:date",
    cardinality: "single",
    required: false,
    uri: "http://example.org/publication-date",
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("PropertiesPane", () => {
  const defaultProps = {
    projectId: "proj-1",
    properties: mockProperties,
    schemes: mockSchemes,
    ontologyClasses: mockOntologyClasses,
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onCreate: vi.fn(),
  };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders table with property data", () => {
    render(<PropertiesPane {...defaultProps} />);

    expect(screen.getByText("Has Author")).toBeInTheDocument();
    expect(screen.getByText("has-author")).toBeInTheDocument();
    expect(screen.getByText("Publication Date")).toBeInTheDocument();
    expect(screen.getByText("publication-date")).toBeInTheDocument();
  });

  it("shows domain class label from ontology", () => {
    render(<PropertiesPane {...defaultProps} />);

    // Both properties have Finding as domain
    const findingCells = screen.getAllByText("Finding");
    expect(findingCells.length).toBeGreaterThanOrEqual(1);
  });

  it("shows scheme title for scheme range", () => {
    render(<PropertiesPane {...defaultProps} />);

    expect(screen.getByText("Animals")).toBeInTheDocument();
  });

  it("shows datatype for datatype range", () => {
    render(<PropertiesPane {...defaultProps} />);

    expect(screen.getByText("xsd:date")).toBeInTheDocument();
  });

  it("shows empty state when no properties", () => {
    render(<PropertiesPane {...defaultProps} properties={[]} />);

    expect(screen.getByText(/no properties/i)).toBeInTheDocument();
  });

  it("calls onCreate when New Property button is clicked", () => {
    render(<PropertiesPane {...defaultProps} />);

    fireEvent.click(screen.getByText("New Property"));

    expect(defaultProps.onCreate).toHaveBeenCalled();
  });

  it("calls onEdit with correct property when edit is clicked", () => {
    render(<PropertiesPane {...defaultProps} />);

    const editButtons = screen.getAllByText("Edit");
    fireEvent.click(editButtons[0]);

    expect(defaultProps.onEdit).toHaveBeenCalledWith(mockProperties[0]);
  });

  it("calls onDelete with correct property when delete is clicked", () => {
    render(<PropertiesPane {...defaultProps} />);

    const deleteButtons = screen.getAllByText("Delete");
    fireEvent.click(deleteButtons[0]);

    expect(defaultProps.onDelete).toHaveBeenCalledWith(mockProperties[0]);
  });
});
