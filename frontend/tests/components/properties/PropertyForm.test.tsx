import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { PropertyForm } from "../../../src/components/properties/PropertyForm";
import { propertiesApi } from "../../../src/api/properties";
import { ApiError } from "../../../src/api/client";
import { ontologyApi } from "../../../src/api/ontology";
import { schemes } from "../../../src/state/schemes";
import type { ConceptScheme, CoreOntology } from "../../../src/types/models";

vi.mock("../../../src/api/properties");
vi.mock("../../../src/api/ontology");

const mockOntology: CoreOntology = {
  classes: [
    { uri: "http://example.org/Person", label: "Person", comment: "A human being" },
    { uri: "http://example.org/Organization", label: "Organization", comment: null },
  ],
  object_properties: [],
  datatype_properties: [],
};

const mockSchemes: ConceptScheme[] = [
  {
    id: "scheme-1",
    project_id: "proj-1",
    title: "Countries",
    description: null,
    uri: "http://example.org/countries",
    publisher: null,
    version: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "scheme-2",
    project_id: "proj-1",
    title: "Languages",
    description: null,
    uri: "http://example.org/languages",
    publisher: null,
    version: null,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("PropertyForm", () => {
  const mockOnSuccess = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(ontologyApi.get).mockResolvedValue(mockOntology);
    schemes.value = mockSchemes;
  });

  describe("rendering", () => {
    it("shows label input", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });
    });

    it("shows identifier input", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/identifier/i)).toBeInTheDocument();
      });
    });

    it("shows domain class dropdown", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/domain/i)).toBeInTheDocument();
      });
    });

    it("populates domain class dropdown from ontology", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByText("Person")).toBeInTheDocument();
        expect(screen.getByText("Organization")).toBeInTheDocument();
      });
    });

    it("shows range type selection", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /scheme/i })).toBeInTheDocument();
        expect(screen.getByRole("radio", { name: /datatype/i })).toBeInTheDocument();
      });
    });

    it("shows cardinality selection", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/single/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/multiple/i)).toBeInTheDocument();
      });
    });

    it("shows required checkbox", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/required/i)).toBeInTheDocument();
      });
    });
  });

  describe("identifier auto-generation", () => {
    it("generates camelCase identifier from label", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });

      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "Date of Birth" } });

      await waitFor(() => {
        const identifierInput = screen.getByLabelText(/identifier/i) as HTMLInputElement;
        expect(identifierInput.value).toBe("dateOfBirth");
      });
    });

    it("allows manual override of identifier", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });

      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "Date of Birth" } });

      const identifierInput = screen.getByLabelText(/identifier/i);
      fireEvent.input(identifierInput, { target: { value: "customId" } });

      // Typing more in label shouldn't change the manually-set identifier
      fireEvent.input(labelInput, { target: { value: "Date of Birth Updated" } });

      await waitFor(() => {
        expect((identifierInput as HTMLInputElement).value).toBe("customId");
      });
    });
  });

  describe("range selection", () => {
    it("shows scheme dropdown when scheme range type selected", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /scheme/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole("radio", { name: /scheme/i }));

      await waitFor(() => {
        expect(screen.getByText("Countries")).toBeInTheDocument();
        expect(screen.getByText("Languages")).toBeInTheDocument();
      });
    });

    it("shows datatype dropdown when datatype range type selected", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      // Datatype is selected by default, so dropdown should already be visible
      await waitFor(() => {
        expect(screen.getByLabelText(/^Range Datatype/)).toBeInTheDocument();
      });

      // The datatype options should be available in the dropdown
      await waitFor(() => {
        expect(screen.getByText("xsd:string")).toBeInTheDocument();
        expect(screen.getByText("xsd:date")).toBeInTheDocument();
      });
    });

    it("enables create button when scheme is selected as range", async () => {
      render(
        <PropertyForm
          projectId="proj-1"
          domainClassUri="http://example.org/Person"
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });

      // Fill in label
      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Nationality" } });

      // Switch to scheme range type
      fireEvent.click(screen.getByRole("radio", { name: /scheme/i }));

      // Select a scheme
      await waitFor(() => {
        expect(screen.getByLabelText(/^Range Scheme/)).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText(/^Range Scheme/), { target: { value: "scheme-1" } });

      // Button should be enabled
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /create/i })).not.toBeDisabled();
      });
    });

    it("submits with scheme range correctly", async () => {
      vi.mocked(propertiesApi.create).mockResolvedValue({
        id: "prop-new",
        project_id: "proj-1",
        identifier: "nationality",
        label: "Nationality",
        description: null,
        domain_class: "http://example.org/Person",
        range_scheme_id: "scheme-1",
        range_scheme: { id: "scheme-1", title: "Countries", uri: "http://example.org/countries" },
        range_datatype: null,
        cardinality: "single",
        required: false,
        uri: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      });

      render(
        <PropertyForm
          projectId="proj-1"
          domainClassUri="http://example.org/Person"
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });

      // Fill in label
      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Nationality" } });

      // Switch to scheme range type
      fireEvent.click(screen.getByRole("radio", { name: /scheme/i }));

      // Select a scheme
      await waitFor(() => {
        expect(screen.getByLabelText(/^Range Scheme/)).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText(/^Range Scheme/), { target: { value: "scheme-1" } });

      // Submit
      fireEvent.click(screen.getByRole("button", { name: /create/i }));

      await waitFor(() => {
        expect(propertiesApi.create).toHaveBeenCalledWith("proj-1", expect.objectContaining({
          label: "Nationality",
          identifier: "nationality",
          domain_class: "http://example.org/Person",
          range_scheme_id: "scheme-1",
          cardinality: "single",
        }));
      });
    });
  });

  describe("form submission", () => {
    it("calls API with form data on submit", async () => {
      vi.mocked(propertiesApi.create).mockResolvedValue({
        id: "prop-new",
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
        uri: "http://example.org/birthDate",
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      });

      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });

      // Fill in form
      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Birth Date" } });
      fireEvent.change(screen.getByLabelText(/domain/i), { target: { value: "http://example.org/Person" } });
      // Datatype is selected by default, so dropdown should already be visible

      await waitFor(() => {
        expect(screen.getByLabelText(/^Range Datatype/)).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText(/^Range Datatype/), { target: { value: "xsd:date" } });

      fireEvent.click(screen.getByRole("button", { name: /create/i }));

      await waitFor(() => {
        expect(propertiesApi.create).toHaveBeenCalledWith("proj-1", expect.objectContaining({
          label: "Birth Date",
          identifier: "birthDate",
          domain_class: "http://example.org/Person",
          range_datatype: "xsd:date",
          cardinality: "single",
          required: false,
        }));
      });
    });

    it("calls onSuccess after successful submission", async () => {
      vi.mocked(propertiesApi.create).mockResolvedValue({
        id: "prop-new",
        project_id: "proj-1",
        identifier: "test",
        label: "Test",
        description: null,
        domain_class: "http://example.org/Person",
        range_scheme_id: null,
        range_scheme: null,
        range_datatype: "xsd:string",
        cardinality: "single",
        required: false,
        uri: "http://example.org/test",
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      });

      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });

      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Test" } });
      fireEvent.change(screen.getByLabelText(/domain/i), { target: { value: "http://example.org/Person" } });
      // Datatype is selected by default, so dropdown should already be visible

      await waitFor(() => {
        expect(screen.getByLabelText(/^Range Datatype/)).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText(/^Range Datatype/), { target: { value: "xsd:string" } });

      fireEvent.click(screen.getByRole("button", { name: /create/i }));

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it("calls onCancel when cancel button clicked", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it("disables create button when required fields are empty", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /create/i })).toBeDisabled();
      });
    });
  });

  describe("validation hints", () => {
    it("shows 'Still needed' hint listing missing fields", async () => {
      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });

      const hint = screen.getByText(/still needed/i);
      expect(hint).toBeInTheDocument();
      expect(hint.textContent).toContain("Label");
      expect(hint.textContent).toContain("Identifier");
      expect(hint.textContent).toContain("Domain class");
      expect(hint.textContent).toContain("Range datatype");
    });

    it("shows specific message on 409 conflict error", async () => {
      vi.mocked(propertiesApi.create).mockRejectedValue(new ApiError(409, "Conflict"));

      render(
        <PropertyForm
          projectId="proj-1"
          domainClassUri="http://example.org/Person"
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });

      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Test" } });

      await waitFor(() => {
        expect(screen.getByLabelText(/^Range Datatype/)).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText(/^Range Datatype/), { target: { value: "xsd:string" } });
      fireEvent.click(screen.getByRole("button", { name: /create/i }));

      await waitFor(() => {
        expect(screen.getByText("A property with this identifier already exists")).toBeInTheDocument();
      });
    });

    it("disables scheme radio when no schemes exist", async () => {
      schemes.value = [];

      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /scheme/i })).toBeInTheDocument();
      });

      expect(screen.getByRole("radio", { name: /scheme/i })).toBeDisabled();
    });

    it("shows 'Create a scheme first' hint when no schemes", async () => {
      schemes.value = [];

      render(<PropertyForm projectId="proj-1" onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      await waitFor(() => {
        expect(screen.getByText(/create a scheme first/i)).toBeInTheDocument();
      });
    });
  });

  describe("with domainClassUri prop", () => {
    it("shows class label instead of dropdown when domainClassUri provided", async () => {
      render(
        <PropertyForm
          projectId="proj-1"
          domainClassUri="http://example.org/Person"
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        // Should show the class label as text, not a dropdown
        expect(screen.getByText("Person")).toBeInTheDocument();
      });

      // Should NOT have a domain class dropdown
      expect(screen.queryByRole("combobox", { name: /domain/i })).not.toBeInTheDocument();
    });

    it("pre-fills domain class in submission when domainClassUri provided", async () => {
      vi.mocked(propertiesApi.create).mockResolvedValue({
        id: "prop-new",
        project_id: "proj-1",
        identifier: "test",
        label: "Test",
        description: null,
        domain_class: "http://example.org/Person",
        range_scheme_id: null,
        range_scheme: null,
        range_datatype: "xsd:string",
        cardinality: "single",
        required: false,
        uri: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      });

      render(
        <PropertyForm
          projectId="proj-1"
          domainClassUri="http://example.org/Person"
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      });

      // Fill in required fields (domain class is pre-filled)
      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Test" } });

      await waitFor(() => {
        expect(screen.getByLabelText(/^Range Datatype/)).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText(/^Range Datatype/), { target: { value: "xsd:string" } });

      fireEvent.click(screen.getByRole("button", { name: /create/i }));

      await waitFor(() => {
        expect(propertiesApi.create).toHaveBeenCalledWith("proj-1", expect.objectContaining({
          domain_class: "http://example.org/Person",
        }));
      });
    });

    it("shows URI when class label not found", async () => {
      render(
        <PropertyForm
          projectId="proj-1"
          domainClassUri="http://example.org/UnknownClass"
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        // Should fall back to showing the URI
        expect(screen.getByText("http://example.org/UnknownClass")).toBeInTheDocument();
      });
    });
  });
});
