import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { PropertyForm, labelToIdentifier } from "../../../src/components/properties/PropertyForm";
import type { ConceptScheme, OntologyClass, Property } from "../../../src/types/models";

vi.mock("../../../src/api/properties", () => ({
  propertiesApi: {
    create: vi.fn(),
    update: vi.fn(),
  },
}));

import { propertiesApi } from "../../../src/api/properties";

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
  { uri: "http://example.org/Intervention", label: "Intervention", comment: null },
];

const mockProperty: Property = {
  id: "prop-1",
  project_id: "proj-1",
  identifier: "has-author",
  label: "Has Author",
  description: "The author of a finding",
  domain_class: "http://example.org/Finding",
  range_scheme_id: "scheme-1",
  range_scheme: { id: "scheme-1", title: "Animals", uri: "http://example.org/animals" },
  range_datatype: null,
  cardinality: "single",
  required: false,
  uri: "http://example.org/has-author",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("labelToIdentifier", () => {
  it("converts label to lowercase kebab-case", () => {
    expect(labelToIdentifier("Has Author")).toBe("has-author");
  });

  it("prefixes with prop- when starts with digit", () => {
    expect(labelToIdentifier("3 months")).toBe("prop-3-months");
  });

  it("strips punctuation", () => {
    expect(labelToIdentifier("Cost ($)")).toBe("cost");
  });

  it("returns empty string for empty input", () => {
    expect(labelToIdentifier("")).toBe("");
  });

  it("strips non-ASCII characters", () => {
    expect(labelToIdentifier("Áccent")).toBe("ccent");
  });

  it("collapses multiple hyphens", () => {
    expect(labelToIdentifier("hello   world")).toBe("hello-world");
  });

  it("trims leading and trailing hyphens", () => {
    expect(labelToIdentifier("  hello  ")).toBe("hello");
  });
});

describe("PropertyForm", () => {
  const defaultProps = {
    projectId: "proj-1",
    schemes: mockSchemes,
    ontologyClasses: mockOntologyClasses,
    onSuccess: vi.fn(),
    onCancel: vi.fn(),
  };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows 'Create Property' button in create mode", () => {
    render(<PropertyForm {...defaultProps} />);
    expect(screen.getByText("Create Property")).toBeInTheDocument();
  });

  it("shows 'Save Changes' button in edit mode", () => {
    render(<PropertyForm {...defaultProps} property={mockProperty} />);
    expect(screen.getByText("Save Changes")).toBeInTheDocument();
  });

  it("auto-generates identifier from label", () => {
    render(<PropertyForm {...defaultProps} />);

    const labelInput = screen.getByLabelText(/Label/);
    fireEvent.input(labelInput, { target: { value: "Has Author" } });

    const identifierInput = screen.getByLabelText(/Identifier/) as HTMLInputElement;
    expect(identifierInput.value).toBe("has-author");
  });

  it("stops auto-generating after manual identifier edit", () => {
    render(<PropertyForm {...defaultProps} />);

    const identifierInput = screen.getByLabelText(/Identifier/);
    fireEvent.input(identifierInput, { target: { value: "custom-id" } });

    const labelInput = screen.getByLabelText(/Label/);
    fireEvent.input(labelInput, { target: { value: "Has Author" } });

    expect((identifierInput as HTMLInputElement).value).toBe("custom-id");
  });

  it("makes identifier read-only in edit mode", () => {
    render(<PropertyForm {...defaultProps} property={mockProperty} />);

    const identifierInput = screen.getByLabelText(/Identifier/);
    expect(identifierInput).toHaveAttribute("readonly");
  });

  it("shows range toggle with Concept Scheme and Datatype options", () => {
    render(<PropertyForm {...defaultProps} />);

    expect(screen.getByLabelText("Concept Scheme")).toBeInTheDocument();
    expect(screen.getByLabelText("Datatype")).toBeInTheDocument();
  });

  it("disables Concept Scheme option when no schemes exist", () => {
    render(<PropertyForm {...defaultProps} schemes={[]} />);

    const schemeRadio = screen.getByRole("radio", { name: /concept scheme/i });
    expect(schemeRadio).toBeDisabled();
  });

  it("shows scheme select when Concept Scheme is selected", () => {
    render(<PropertyForm {...defaultProps} />);

    const schemeRadio = screen.getByLabelText("Concept Scheme");
    fireEvent.click(schemeRadio);

    expect(screen.getByText("Animals")).toBeInTheDocument();
  });

  it("shows datatype select when Datatype is selected", () => {
    render(<PropertyForm {...defaultProps} />);

    const datatypeRadio = screen.getByLabelText("Datatype");
    fireEvent.click(datatypeRadio);

    expect(screen.getByText("xsd:string")).toBeInTheDocument();
  });

  it("shows inline error for invalid identifier", () => {
    render(<PropertyForm {...defaultProps} />);

    const identifierInput = screen.getByLabelText(/Identifier/);
    fireEvent.input(identifierInput, { target: { value: "123-bad" } });

    expect(screen.getByText(/must start with a letter/i)).toBeInTheDocument();
  });

  it("populates form fields from existing property", () => {
    render(<PropertyForm {...defaultProps} property={mockProperty} />);

    expect(screen.getByDisplayValue("Has Author")).toBeInTheDocument();
    expect(screen.getByDisplayValue("has-author")).toBeInTheDocument();
    expect(screen.getByDisplayValue("The author of a finding")).toBeInTheDocument();
  });

  it("calls propertiesApi.create on submit in create mode", async () => {
    vi.mocked(propertiesApi.create).mockResolvedValue(mockProperty);

    render(<PropertyForm {...defaultProps} />);

    fireEvent.input(screen.getByLabelText(/Label/), { target: { value: "Has Author" } });

    // Select domain class
    const domainSelect = screen.getByLabelText(/Applies to/);
    fireEvent.change(domainSelect, { target: { value: "http://example.org/Finding" } });

    // Select range: datatype
    fireEvent.click(screen.getByLabelText("Datatype"));
    const datatypeSelect = screen.getByLabelText(/Datatype select/);
    fireEvent.change(datatypeSelect, { target: { value: "xsd:string" } });

    fireEvent.submit(screen.getByRole("form"));

    // Wait for async submit
    await waitFor(() => {
      expect(propertiesApi.create).toHaveBeenCalledWith("proj-1", expect.objectContaining({
        label: "Has Author",
        identifier: "has-author",
        domain_class: "http://example.org/Finding",
        range_datatype: "xsd:string",
      }));
    });
  });

  it("calls propertiesApi.update on submit in edit mode", async () => {
    vi.mocked(propertiesApi.update).mockResolvedValue(mockProperty);

    render(<PropertyForm {...defaultProps} property={mockProperty} />);

    fireEvent.input(screen.getByLabelText(/Label/), { target: { value: "Updated Label" } });
    fireEvent.submit(screen.getByRole("form"));

    await waitFor(() => {
      expect(propertiesApi.update).toHaveBeenCalledWith("prop-1", expect.objectContaining({
        label: "Updated Label",
      }));
    });
  });

  it("displays 409 error as duplicate identifier message", async () => {
    const { ApiError } = await import("../../../src/api/client");
    vi.mocked(propertiesApi.create).mockRejectedValue(
      new ApiError(409, "Property with this identifier already exists")
    );

    render(<PropertyForm {...defaultProps} />);

    fireEvent.input(screen.getByLabelText(/Label/), { target: { value: "Test" } });
    const domainSelect = screen.getByLabelText(/Applies to/);
    fireEvent.change(domainSelect, { target: { value: "http://example.org/Finding" } });
    fireEvent.click(screen.getByLabelText("Datatype"));
    fireEvent.change(screen.getByLabelText(/Datatype select/), { target: { value: "xsd:string" } });

    fireEvent.submit(screen.getByRole("form"));

    await waitFor(() => {
      expect(screen.getByText(/already exists/i)).toBeInTheDocument();
    });
  });
});
