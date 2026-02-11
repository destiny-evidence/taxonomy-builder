import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { PropertyDetail } from "../../../src/components/properties/PropertyDetail";
import { propertiesApi } from "../../../src/api/properties";
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

    it("displays domain class", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText("Person")).toBeInTheDocument();
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

      // Find the close button (×) in the header
      const header = screen.getByText("Birth Date").closest(".property-detail__header");
      const closeButton = header?.querySelector("button");
      fireEvent.click(closeButton!);

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

    it("shows domain class dropdown pre-selected in edit mode", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const select = screen.getByRole("combobox", { name: /domain/i });
      expect(select).toBeInTheDocument();
      expect(select).toHaveValue("http://example.org/Person");
    });

    it("allows changing domain class", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const select = screen.getByRole("combobox", { name: /domain/i });
      fireEvent.change(select, { target: { value: "http://example.org/Organization" } });
      expect(select).toHaveValue("http://example.org/Organization");
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

    it("shows datatype dropdown when range type is datatype", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const select = screen.getByRole("combobox", { name: /range datatype/i });
      expect(select).toHaveValue("xsd:date");
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
        domain_class: "http://example.org/Organization",
        cardinality: "multiple",
        required: true,
      });

      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Change domain class
      fireEvent.change(screen.getByRole("combobox", { name: /domain/i }), {
        target: { value: "http://example.org/Organization" },
      });
      // Change cardinality
      fireEvent.click(screen.getByRole("radio", { name: /multiple values/i }));
      // Toggle required
      fireEvent.click(screen.getByRole("checkbox", { name: /required/i }));

      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(propertiesApi.update).toHaveBeenCalledWith("prop-1", {
          label: "Birth Date",
          description: "The date when a person was born",
          domain_class: "http://example.org/Organization",
          range_scheme_id: null,
          range_datatype: "xsd:date",
          cardinality: "multiple",
          required: true,
        });
      });
    });

    it("sends scheme range when range type is scheme", async () => {
      vi.mocked(propertiesApi.update).mockResolvedValue(mockSchemeProperty);

      render(<PropertyDetail property={mockSchemeProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(propertiesApi.update).toHaveBeenCalledWith("prop-2", {
          label: "Nationality",
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
      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      });
    });

    it("shows error message on save failure", async () => {
      vi.mocked(propertiesApi.update).mockRejectedValue(new Error("Network error"));

      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });
  });
});
