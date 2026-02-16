import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { PropertyDetail } from "../../../src/components/properties/PropertyDetail";
import { propertiesApi } from "../../../src/api/properties";
import { ApiError } from "../../../src/api/client";
import { ontology } from "../../../src/state/ontology";
import { schemes } from "../../../src/state/schemes";
import type { Property } from "../../../src/types/models";

vi.mock("../../../src/api/properties");

const mockProperty: Property = {
  id: "prop-1",
  project_id: "proj-1",
  identifier: "birthDate",
  label: "Birth Date",
  description: "The date when a person was born",
  domain_class: "http://example.org/Person",
  range_scheme_id: null,
  range_scheme: null,
  range_datatype: "xsd:date",
  cardinality: "single",
  required: false,
  uri: "http://example.org/birthDate",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockSchemeProperty: Property = {
  ...mockProperty,
  id: "prop-2",
  identifier: "nationality",
  label: "Nationality",
  description: null,
  range_scheme_id: "scheme-1",
  range_scheme: { id: "scheme-1", title: "Countries", uri: "http://example.org/countries" },
  range_datatype: null,
  cardinality: "multiple",
  required: true,
};

describe("PropertyDetail", () => {
  const mockOnRefresh = vi.fn();
  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    // Set up ontology classes for edit mode dropdowns
    ontology.value = {
      classes: [
        { uri: "http://example.org/Person", label: "Person", comment: null },
        { uri: "http://example.org/Organization", label: "Organization", comment: null },
      ],
      object_properties: [],
      datatype_properties: [],
    };
    // Set up schemes for edit mode dropdowns
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
      {
        id: "scheme-2",
        project_id: "proj-1",
        title: "Languages",
        description: null,
        uri: "http://example.org/languages",
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
    ];
  });

  afterEach(() => {
    ontology.value = null;
    schemes.value = [];
  });

  describe("view mode", () => {
    it("displays property label as heading", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText("Birth Date")).toBeInTheDocument();
    });

    it("displays identifier", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText("birthDate")).toBeInTheDocument();
    });

    it("displays description when present", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText("The date when a person was born")).toBeInTheDocument();
    });

    it("does not display description section when null", () => {
      render(<PropertyDetail property={mockSchemeProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.queryByText("Description")).not.toBeInTheDocument();
    });

    it("displays class label (not 'Domain')", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText("Class")).toBeInTheDocument();
      expect(screen.getByText("Person")).toBeInTheDocument();
      expect(screen.queryByText("Domain")).not.toBeInTheDocument();
    });

    it("falls back to local name from URI when class not in ontology", () => {
      const unknownClassProperty = {
        ...mockProperty,
        domain_class: "http://example.org/UnknownThing",
      };
      render(<PropertyDetail property={unknownClassProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText("UnknownThing")).toBeInTheDocument();
    });

    it("displays cardinality", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText(/single/i)).toBeInTheDocument();
    });

    it("displays required status", () => {
      render(<PropertyDetail property={mockSchemeProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText(/yes/i)).toBeInTheDocument();
    });

    it("shows Edit button", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
    });

    it("shows Delete button", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
    });

    it("shows close button in header", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      // Close button is in the header next to the title
      const header = screen.getByText("Birth Date").closest(".property-detail__header");
      expect(header?.querySelector("button")).toBeInTheDocument();
    });

    it("calls onClose when close button clicked", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      const closeButton = screen.getByRole("button", { name: "Close" });
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe("delete functionality", () => {
    it("shows confirmation dialog when delete is clicked", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /delete/i }));

      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    it("calls API and callbacks on delete confirm", async () => {
      vi.mocked(propertiesApi.delete).mockResolvedValue(undefined);

      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /delete/i }));
      fireEvent.click(screen.getByRole("button", { name: /confirm/i }));

      await waitFor(() => {
        expect(propertiesApi.delete).toHaveBeenCalledWith("prop-1");
      });

      await waitFor(() => {
        expect(mockOnRefresh).toHaveBeenCalled();
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it("closes confirmation dialog on cancel", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /delete/i }));
      // Dialog should be open
      const dialog = document.querySelector("dialog");
      expect(dialog).toHaveAttribute("open");

      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

      // Dialog should be closed (no open attribute)
      expect(dialog).not.toHaveAttribute("open");
    });
  });

  describe("edit mode", () => {
    it("switches to edit mode when Edit button clicked", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Should show Cancel and Save buttons
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
    });

    it("shows input for label pre-filled with current value", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByDisplayValue("Birth Date")).toBeInTheDocument();
    });

    it("shows identifier as read-only text in edit mode", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Identifier should be displayed as text, not an editable input
      expect(screen.getByText("birthDate")).toBeInTheDocument();
      expect(screen.queryByDisplayValue("birthDate")).not.toBeInTheDocument();
    });

    it("shows textarea for description", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByDisplayValue("The date when a person was born")).toBeInTheDocument();
    });

    it("shows class as read-only text in edit mode", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByText("Person")).toBeInTheDocument();
      expect(screen.queryByRole("combobox", { name: /class/i })).not.toBeInTheDocument();
    });

    it("shows range type radios in edit mode for datatype property", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const datatypeRadio = screen.getByRole("radio", { name: /datatype/i });
      const schemeRadio = screen.getByRole("radio", { name: /scheme/i });
      expect(datatypeRadio).toBeChecked();
      expect(schemeRadio).not.toBeChecked();
    });

    it("shows range type radios in edit mode for scheme property", () => {
      render(<PropertyDetail property={mockSchemeProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const schemeRadio = screen.getByRole("radio", { name: /scheme/i });
      const datatypeRadio = screen.getByRole("radio", { name: /datatype/i });
      expect(schemeRadio).toBeChecked();
      expect(datatypeRadio).not.toBeChecked();
    });

    it("shows datatype dropdown with friendly names", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const select = screen.getByRole("combobox", { name: /range datatype/i });
      expect(select).toHaveValue("xsd:date");

      // Options should show friendly names, not xsd prefixes
      const options = select.querySelectorAll("option");
      const labels = Array.from(options).map((o) => o.textContent).filter(Boolean);
      expect(labels).toContain("Date");
      expect(labels).not.toContain("xsd:date");
      expect(labels).toContain("Text");
      expect(labels).not.toContain("xsd:string");
    });

    it("shows scheme dropdown when range type is scheme", () => {
      render(<PropertyDetail property={mockSchemeProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const select = screen.getByRole("combobox", { name: /range scheme/i });
      expect(select).toHaveValue("scheme-1");
    });

    it("toggles between scheme and datatype range dropdowns", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Initially shows datatype dropdown
      expect(screen.getByRole("combobox", { name: /range datatype/i })).toBeInTheDocument();
      expect(screen.queryByRole("combobox", { name: /range scheme/i })).not.toBeInTheDocument();

      // Switch to scheme
      fireEvent.click(screen.getByRole("radio", { name: /scheme/i }));

      expect(screen.getByRole("combobox", { name: /range scheme/i })).toBeInTheDocument();
      expect(screen.queryByRole("combobox", { name: /range datatype/i })).not.toBeInTheDocument();
    });

    it("shows cardinality radios pre-selected in edit mode", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByRole("radio", { name: /single value/i })).toBeChecked();
      expect(screen.getByRole("radio", { name: /multiple values/i })).not.toBeChecked();
    });

    it("allows changing cardinality", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      fireEvent.click(screen.getByRole("radio", { name: /multiple values/i }));
      expect(screen.getByRole("radio", { name: /multiple values/i })).toBeChecked();
      expect(screen.getByRole("radio", { name: /single value/i })).not.toBeChecked();
    });

    it("shows required checkbox in edit mode", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const checkbox = screen.getByRole("checkbox", { name: /required/i });
      expect(checkbox).not.toBeChecked();
    });

    it("allows toggling required checkbox", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const checkbox = screen.getByRole("checkbox", { name: /required/i });
      fireEvent.click(checkbox);
      expect(checkbox).toBeChecked();
    });

    it("exits edit mode on cancel without saving", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Modify a field
      const labelInput = screen.getByDisplayValue("Birth Date");
      fireEvent.input(labelInput, { target: { value: "Modified Label" } });

      // Cancel
      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

      // Should be back in view mode with original values
      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      expect(screen.getByText("Birth Date")).toBeInTheDocument();
    });

    it("disables save when label is empty", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByDisplayValue("Birth Date");
      fireEvent.input(labelInput, { target: { value: "" } });

      expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
    });

    it("sends all config fields in update payload on save", async () => {
      vi.mocked(propertiesApi.update).mockResolvedValue({
        ...mockProperty,
        label: "Updated Label",
      });

      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByDisplayValue("Birth Date");
      fireEvent.input(labelInput, { target: { value: "Updated Label" } });

      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(propertiesApi.update).toHaveBeenCalledWith("prop-1", {
          label: "Updated Label",
          description: "The date when a person was born",
          domain_class: "http://example.org/Person",
          range_scheme_id: null,
          range_datatype: "xsd:date",
          cardinality: "single",
          required: false,
        });
      });

      await waitFor(() => {
        expect(mockOnRefresh).toHaveBeenCalled();
      });
    });

    it("sends changed config fields on save", async () => {
      vi.mocked(propertiesApi.update).mockResolvedValue({
        ...mockProperty,
        cardinality: "multiple",
        required: true,
      });

      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Change cardinality
      fireEvent.click(screen.getByRole("radio", { name: /multiple values/i }));
      // Toggle required
      fireEvent.click(screen.getByRole("checkbox", { name: /required/i }));

      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(propertiesApi.update).toHaveBeenCalledWith("prop-1", {
          label: "Birth Date",
          description: "The date when a person was born",
          domain_class: "http://example.org/Person",
          range_scheme_id: null,
          range_datatype: "xsd:date",
          cardinality: "multiple",
          required: true,
        });
      });
    });

    it("sends scheme range when range type is scheme", async () => {
      vi.mocked(propertiesApi.update).mockResolvedValue({
        ...mockSchemeProperty,
        label: "Nationality Updated",
      });

      render(<PropertyDetail property={mockSchemeProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByDisplayValue("Nationality");
      fireEvent.input(labelInput, { target: { value: "Nationality Updated" } });

      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(propertiesApi.update).toHaveBeenCalledWith("prop-2", {
          label: "Nationality Updated",
          description: null,
          domain_class: "http://example.org/Person",
          range_scheme_id: "scheme-1",
          range_datatype: null,
          cardinality: "multiple",
          required: true,
        });
      });
    });

    it("shows loading state on save button while saving", async () => {
      vi.mocked(propertiesApi.update).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByDisplayValue("Birth Date");
      fireEvent.input(labelInput, { target: { value: "Changed" } });

      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /saving/i })).toBeDisabled();
      });
    });

    it("exits edit mode after successful save", async () => {
      vi.mocked(propertiesApi.update).mockResolvedValue({
        ...mockProperty,
        label: "Updated Label",
      });

      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByDisplayValue("Birth Date");
      fireEvent.input(labelInput, { target: { value: "Updated Label" } });

      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      });
    });

    it("shows error message on save failure", async () => {
      vi.mocked(propertiesApi.update).mockRejectedValue(new Error("Network error"));

      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByDisplayValue("Birth Date");
      fireEvent.input(labelInput, { target: { value: "Changed" } });

      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    it("disables save when no changes made", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
    });

    it("shows 'No changes to save' hint when no changes made", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByText("No changes to save")).toBeInTheDocument();
    });

    it("shows specific message on 409 conflict error", async () => {
      vi.mocked(propertiesApi.update).mockRejectedValue(new ApiError(409, "Conflict"));

      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const labelInput = screen.getByDisplayValue("Birth Date");
      fireEvent.input(labelInput, { target: { value: "Changed" } });

      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(screen.getByText("A property with this identifier already exists")).toBeInTheDocument();
      });
    });
  });

  describe("create mode", () => {
    function renderCreate(overrides: Record<string, unknown> = {}) {
      return render(
        <PropertyDetail
          mode="create"
          projectId="proj-1"
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
          onRefresh={mockOnRefresh}
          {...overrides}
        />
      );
    }

    it("shows 'New Property' as title", () => {
      renderCreate();
      expect(screen.getByText("New Property")).toBeInTheDocument();
    });

    it("shows all form fields", () => {
      renderCreate({ domainClassUri: "http://example.org/Person" });

      expect(screen.getByLabelText(/label/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/identifier/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(screen.getByText("Class")).toBeInTheDocument();
      expect(screen.getByText("Person")).toBeInTheDocument();
      expect(screen.queryByRole("combobox", { name: /class/i })).not.toBeInTheDocument();
      expect(screen.getByRole("radio", { name: /scheme/i })).toBeInTheDocument();
      expect(screen.getByRole("radio", { name: /datatype/i })).toBeInTheDocument();
      expect(screen.getByRole("radio", { name: /single value/i })).toBeInTheDocument();
      expect(screen.getByRole("radio", { name: /multiple values/i })).toBeInTheDocument();
      expect(screen.getByRole("checkbox", { name: /required/i })).toBeInTheDocument();
    });

    it("shows editable identifier input (not read-only text)", () => {
      renderCreate();

      const identifierInput = screen.getByLabelText(/identifier/i);
      expect(identifierInput.tagName).toBe("INPUT");
    });

    it("does not show Delete button", () => {
      renderCreate();
      expect(screen.queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
    });

    it("does not show metadata (created_at, updated_at)", () => {
      renderCreate();
      expect(screen.queryByText(/created/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/updated/i)).not.toBeInTheDocument();
    });

    it("shows 'Create Property' button", () => {
      renderCreate();
      expect(screen.getByRole("button", { name: /create property/i })).toBeInTheDocument();
    });

    it("does not show 'Save' button", () => {
      renderCreate();
      expect(screen.queryByRole("button", { name: /^save$/i })).not.toBeInTheDocument();
    });

    it("shows Cancel button", () => {
      renderCreate();
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    });

    it("calls onCancel when Cancel clicked", () => {
      renderCreate();
      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
      expect(mockOnCancel).toHaveBeenCalled();
    });

    it("auto-generates identifier from label", async () => {
      renderCreate();

      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "My Cool Property" } });

      await waitFor(() => {
        const identifierInput = screen.getByLabelText(/identifier/i) as HTMLInputElement;
        expect(identifierInput.value).toBe("myCoolProperty");
      });
    });

    it("stops auto-generating after manual identifier edit", async () => {
      renderCreate();

      const labelInput = screen.getByLabelText(/label/i);
      fireEvent.input(labelInput, { target: { value: "My Cool Property" } });

      const identifierInput = screen.getByLabelText(/identifier/i);
      fireEvent.input(identifierInput, { target: { value: "customId" } });

      // Changing label again should not overwrite
      fireEvent.input(labelInput, { target: { value: "Another Label" } });

      await waitFor(() => {
        expect((identifierInput as HTMLInputElement).value).toBe("customId");
      });
    });

    it("shows validation error for invalid identifier", () => {
      renderCreate();

      const identifierInput = screen.getByLabelText(/identifier/i);
      fireEvent.input(identifierInput, { target: { value: "123invalid" } });

      expect(screen.getByText(/must start with a letter/i)).toBeInTheDocument();
    });

    it("calls propertiesApi.create on submit with valid fields", async () => {
      vi.mocked(propertiesApi.create).mockResolvedValue({
        id: "prop-new",
        project_id: "proj-1",
        identifier: "myCoolProperty",
        label: "My Cool Property",
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

      renderCreate({ domainClassUri: "http://example.org/Person" });

      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "My Cool Property" } });
      fireEvent.change(screen.getByRole("combobox", { name: /range datatype/i }), {
        target: { value: "xsd:string" },
      });

      fireEvent.click(screen.getByRole("button", { name: /create property/i }));

      await waitFor(() => {
        expect(propertiesApi.create).toHaveBeenCalledWith("proj-1", expect.objectContaining({
          label: "My Cool Property",
          identifier: "myCoolProperty",
          domain_class: "http://example.org/Person",
          range_datatype: "xsd:string",
          cardinality: "single",
          required: false,
        }));
      });
    });

    it("calls onSuccess after successful create", async () => {
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

      renderCreate({ domainClassUri: "http://example.org/Person" });

      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Test" } });
      fireEvent.change(screen.getByRole("combobox", { name: /range datatype/i }), {
        target: { value: "xsd:string" },
      });

      fireEvent.click(screen.getByRole("button", { name: /create property/i }));

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it("shows loading state during submission", async () => {
      vi.mocked(propertiesApi.create).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      renderCreate({ domainClassUri: "http://example.org/Person" });

      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Test" } });
      fireEvent.change(screen.getByRole("combobox", { name: /range datatype/i }), {
        target: { value: "xsd:string" },
      });

      fireEvent.click(screen.getByRole("button", { name: /create property/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /creating/i })).toBeDisabled();
      });
    });

    it("shows error message on API failure", async () => {
      vi.mocked(propertiesApi.create).mockRejectedValue(new Error("Network error"));

      renderCreate({ domainClassUri: "http://example.org/Person" });

      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Test" } });
      fireEvent.change(screen.getByRole("combobox", { name: /range datatype/i }), {
        target: { value: "xsd:string" },
      });

      fireEvent.click(screen.getByRole("button", { name: /create property/i }));

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    it("disables Create button when required fields missing", () => {
      renderCreate();
      expect(screen.getByRole("button", { name: /create property/i })).toBeDisabled();
    });

    it("shows 'Still needed' hints after user interacts with form", () => {
      renderCreate();
      expect(screen.queryByText(/still needed/i)).not.toBeInTheDocument();

      // Type something in description to trigger formTouched, leaving required fields empty
      fireEvent.input(screen.getByLabelText(/description/i), { target: { value: "test" } });

      const hint = screen.getByText(/still needed/i);
      expect(hint).toBeInTheDocument();
      expect(hint.textContent).toContain("Label");
    });

    it("shows class as read-only text when domainClassUri provided", () => {
      renderCreate({ domainClassUri: "http://example.org/Person" });

      expect(screen.getByText("Class")).toBeInTheDocument();
      expect(screen.getByText("Person")).toBeInTheDocument();
      expect(screen.queryByRole("combobox", { name: /class/i })).not.toBeInTheDocument();
    });

    it("shows 409 conflict error message", async () => {
      vi.mocked(propertiesApi.create).mockRejectedValue(new ApiError(409, "Conflict"));

      renderCreate({ domainClassUri: "http://example.org/Person" });

      fireEvent.input(screen.getByLabelText(/label/i), { target: { value: "Test" } });
      fireEvent.change(screen.getByRole("combobox", { name: /range datatype/i }), {
        target: { value: "xsd:string" },
      });

      fireEvent.click(screen.getByRole("button", { name: /create property/i }));

      await waitFor(() => {
        expect(screen.getByText("A property with this identifier already exists")).toBeInTheDocument();
      });
    });
  });
});
