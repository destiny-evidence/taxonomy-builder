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
});
