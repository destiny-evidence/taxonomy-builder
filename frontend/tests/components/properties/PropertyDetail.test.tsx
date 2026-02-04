import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { PropertyDetail } from "../../../src/components/properties/PropertyDetail";
import { propertiesApi } from "../../../src/api/properties";
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
  const mockOnSchemeNavigate = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
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

    it("displays range datatype for datatype properties", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText("xsd:date")).toBeInTheDocument();
    });

    it("displays range scheme title for scheme properties", () => {
      render(<PropertyDetail property={mockSchemeProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      expect(screen.getByText("Countries")).toBeInTheDocument();
    });

    it("makes range scheme clickable when onSchemeNavigate provided", () => {
      render(
        <PropertyDetail
          property={mockSchemeProperty}
          onRefresh={mockOnRefresh}
          onClose={mockOnClose}
          onSchemeNavigate={mockOnSchemeNavigate}
        />
      );

      const schemeLink = screen.getByRole("button", { name: "Countries" });
      fireEvent.click(schemeLink);

      expect(mockOnSchemeNavigate).toHaveBeenCalledWith("scheme-1");
    });

    it("does not make range scheme clickable when onSchemeNavigate not provided", () => {
      render(<PropertyDetail property={mockSchemeProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      // Should be text, not a button
      expect(screen.queryByRole("button", { name: "Countries" })).not.toBeInTheDocument();
      expect(screen.getByText("Countries")).toBeInTheDocument();
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

    it("shows input for identifier pre-filled with current value", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByDisplayValue("birthDate")).toBeInTheDocument();
    });

    it("shows textarea for description", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByDisplayValue("The date when a person was born")).toBeInTheDocument();
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

    it("shows validation error for invalid identifier", () => {
      render(<PropertyDetail property={mockProperty} onRefresh={mockOnRefresh} onClose={mockOnClose} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const identifierInput = screen.getByDisplayValue("birthDate");
      fireEvent.input(identifierInput, { target: { value: "123-invalid" } });

      expect(screen.getByText(/must start with a letter/i)).toBeInTheDocument();
    });

    it("calls API and refreshes on save", async () => {
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
          identifier: "birthDate",
          description: "The date when a person was born",
        });
      });

      await waitFor(() => {
        expect(mockOnRefresh).toHaveBeenCalled();
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
