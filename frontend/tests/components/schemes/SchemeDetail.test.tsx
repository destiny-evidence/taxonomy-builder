import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { SchemeDetail } from "../../../src/components/schemes/SchemeDetail";
import { schemes } from "../../../src/state/schemes";
import { schemesApi } from "../../../src/api/schemes";
import type { ConceptScheme } from "../../../src/types/models";

vi.mock("../../../src/api/schemes");

const mockScheme: ConceptScheme = {
  id: "scheme-1",
  project_id: "proj-1",
  title: "Animals",
  description: "Animal taxonomy",
  uri: "http://example.org/animals",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("SchemeDetail", () => {
  const mockOnRefresh = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    schemes.value = [mockScheme];
  });

  it("displays scheme details", () => {
    render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

    // Title is not shown in read-only mode to avoid repetition (it's in TreePane header)
    expect(screen.getByText("http://example.org/animals")).toBeInTheDocument();
    expect(screen.getByText("Animal taxonomy")).toBeInTheDocument();
  });

  it("displays all scheme fields including timestamps", () => {
    render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

    expect(screen.getByText(/created/i)).toBeInTheDocument();
    expect(screen.getByText(/updated/i)).toBeInTheDocument();
  });

  it("hides null/empty optional fields in read-only view", () => {
    render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

    // Version is removed, so it shouldn't be displayed in read-only mode
    expect(screen.queryByText(/version/i)).not.toBeInTheDocument();
  });

  it("shows all fields including null ones in edit mode", () => {
    render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));

    // Should show labels for all fields in edit mode
    expect(screen.getByText(/description/i)).toBeInTheDocument();
  });

  it("displays Edit button in read-only mode", () => {
    render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

    expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
  });

  it("switches to edit mode when Edit button is clicked", () => {
    render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));

    expect(screen.queryByRole("button", { name: /^edit$/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /save changes/i })).toBeInTheDocument();
  });

  it("shows title input field in edit mode", () => {
    render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));

    const titleInput = screen.getByDisplayValue("Animals");
    expect(titleInput).toBeInTheDocument();
    expect(titleInput.tagName.toLowerCase()).toBe("input");
  });

  it("updates title in draft when input changes", () => {
    render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));

    const titleInput = screen.getByDisplayValue("Animals");
    fireEvent.input(titleInput, { target: { value: "Updated Animals" } });

    expect(titleInput).toHaveValue("Updated Animals");
  });

  it("exits edit mode and discards changes when Cancel is clicked", () => {
    render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));

    const titleInput = screen.getByDisplayValue("Animals");
    fireEvent.input(titleInput, { target: { value: "Updated Animals" } });

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
    // Verify we're back in read-only mode (URI field is visible)
    expect(screen.getByText("http://example.org/animals")).toBeInTheDocument();
  });

  it("exits edit mode when scheme changes", () => {
    const { rerender } = render(
      <SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />
    );

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));

    const differentScheme = { ...mockScheme, id: "scheme-2", title: "Plants" };
    rerender(<SchemeDetail scheme={differentScheme} onRefresh={mockOnRefresh} />);

    expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /cancel/i })).not.toBeInTheDocument();
  });

  describe("Saving changes", () => {
    beforeEach(() => {
      vi.mocked(schemesApi.update).mockResolvedValue({
        ...mockScheme,
        title: "Updated Title",
      });
    });

    it("displays input fields for all editable properties", () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      expect(screen.getByDisplayValue("Animals")).toBeInTheDocument();
      expect(screen.getByDisplayValue("http://example.org/animals")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Animal taxonomy")).toBeInTheDocument();
      expect(screen.getAllByRole("textbox").length).toBeGreaterThanOrEqual(3);
    });

    it("calls API with updated data when Save is clicked", async () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "Updated Animals" } });

      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(schemesApi.update).toHaveBeenCalledWith("scheme-1", {
          title: "Updated Animals",
          uri: "http://example.org/animals",
          description: "Animal taxonomy",
                        });
      });
    });

    it("exits edit mode after successful save", async () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      });
    });

    it("calls onRefresh after successful save", async () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(mockOnRefresh).toHaveBeenCalled();
      });
    });

    it("updates schemes signal after successful save", async () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      const initialSchemesCount = schemes.value.length;

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      });

      expect(schemes.value.length).toBe(initialSchemesCount);
    });

    it("shows loading state on Save button while saving", async () => {
      vi.mocked(schemesApi.update).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        const saveButton = screen.getByRole("button", { name: /saving/i });
        expect(saveButton).toBeDisabled();
      });
    });
  });

  describe("Validation", () => {
    it("shows error when title is empty", () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "" } });

      expect(screen.getByText(/title is required/i)).toBeInTheDocument();
    });

    it("shows error for malformed URI", () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const uriInput = screen.getByDisplayValue("http://example.org/animals");
      fireEvent.input(uriInput, { target: { value: "not-a-url" } });

      expect(screen.getByText(/must be a valid url/i)).toBeInTheDocument();
    });

    it("accepts empty URI", () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const uriInput = screen.getByDisplayValue("http://example.org/animals");
      fireEvent.input(uriInput, { target: { value: "" } });

      expect(screen.queryByText(/must be a valid url/i)).not.toBeInTheDocument();
    });

    it("disables Save button when validation fails", () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "" } });

      const saveButton = screen.getByRole("button", { name: /save changes/i });
      expect(saveButton).toBeDisabled();
    });

    it("clears validation error when field is corrected", () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "" } });
      expect(screen.getByText(/title is required/i)).toBeInTheDocument();

      fireEvent.input(titleInput, { target: { value: "New Title" } });
      expect(screen.queryByText(/title is required/i)).not.toBeInTheDocument();
    });

    it("allows http and https URIs", () => {
      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const uriInput = screen.getByDisplayValue("http://example.org/animals");

      fireEvent.input(uriInput, { target: { value: "https://example.org/test" } });
      expect(screen.queryByText(/must be a valid url/i)).not.toBeInTheDocument();

      fireEvent.input(uriInput, { target: { value: "http://example.org/test" } });
      expect(screen.queryByText(/must be a valid url/i)).not.toBeInTheDocument();
    });
  });

  describe("Error handling", () => {
    it("displays error message when save fails", async () => {
      const errorMessage = "Network error occurred";
      vi.mocked(schemesApi.update).mockRejectedValue(new Error(errorMessage));

      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    });

    it("clears error message on retry", async () => {
      const errorMessage = "Network error occurred";
      vi.mocked(schemesApi.update)
        .mockRejectedValueOnce(new Error(errorMessage))
        .mockResolvedValueOnce({ ...mockScheme });

      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(screen.queryByText(errorMessage)).not.toBeInTheDocument();
      });
    });

    it("allows editing after save failure", async () => {
      vi.mocked(schemesApi.update).mockRejectedValue(new Error("Save failed"));

      render(<SchemeDetail scheme={mockScheme} onRefresh={mockOnRefresh} />);

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(screen.getByText(/save failed/i)).toBeInTheDocument();
      });

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "New Title" } });
      expect(titleInput).toHaveValue("New Title");
    });
  });
});
