import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { SchemesPane } from "../../../src/components/workspace/SchemesPane";
import { currentProject } from "../../../src/state/projects";
import { schemes } from "../../../src/state/schemes";
import { schemesApi } from "../../../src/api/schemes";
import type { Project, ConceptScheme } from "../../../src/types/models";

vi.mock("../../../src/api/schemes");

const mockProject: Project = {
  id: "proj-1",
  name: "Project One",
  description: "First project",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockSchemes: ConceptScheme[] = [
  {
    id: "scheme-1",
    project_id: "proj-1",
    title: "Animals",
    description: "Animal taxonomy",
    uri: "http://example.org/animals",
    publisher: null,
    version: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "scheme-2",
    project_id: "proj-1",
    title: "Plants",
    description: "Plant taxonomy",
    uri: "http://example.org/plants",
    publisher: null,
    version: null,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("SchemesPane", () => {
  const mockOnSchemeSelect = vi.fn();
  const mockOnNewScheme = vi.fn();
  const mockOnImport = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    currentProject.value = mockProject;
    schemes.value = mockSchemes;
  });

  it("renders current project name as heading", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onNewScheme={mockOnNewScheme}
        onImport={mockOnImport}
      />
    );

    expect(screen.getByText("Project One")).toBeInTheDocument();
  });

  it("renders back link to projects", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onNewScheme={mockOnNewScheme}
        onImport={mockOnImport}
      />
    );

    const backLink = screen.getByRole("link", { name: /projects/i });
    expect(backLink).toHaveAttribute("href", "/projects");
  });

  it("lists schemes for the current project", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onNewScheme={mockOnNewScheme}
        onImport={mockOnImport}
      />
    );

    expect(screen.getByText("Animals")).toBeInTheDocument();
    expect(screen.getByText("Plants")).toBeInTheDocument();
  });

  it("highlights the current scheme", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId="scheme-1"
        onSchemeSelect={mockOnSchemeSelect}
        onNewScheme={mockOnNewScheme}
        onImport={mockOnImport}
      />
    );

    const schemeList = screen.getByRole("button", { name: "Animals" });
    expect(schemeList).toHaveClass("schemes-pane__item--selected");
  });

  it("calls onSchemeSelect when scheme is clicked", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onNewScheme={mockOnNewScheme}
        onImport={mockOnImport}
      />
    );

    fireEvent.click(screen.getByText("Animals"));

    expect(mockOnSchemeSelect).toHaveBeenCalledWith("scheme-1");
  });

  it("shows empty state when project has no schemes", () => {
    schemes.value = [];

    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onNewScheme={mockOnNewScheme}
        onImport={mockOnImport}
      />
    );

    expect(screen.getByText(/no schemes/i)).toBeInTheDocument();
  });

  it("calls onNewScheme when New Scheme button is clicked", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onNewScheme={mockOnNewScheme}
        onImport={mockOnImport}
      />
    );

    fireEvent.click(screen.getByText("+ New Scheme"));

    expect(mockOnNewScheme).toHaveBeenCalled();
  });

  it("calls onImport when Import button is clicked", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onNewScheme={mockOnNewScheme}
        onImport={mockOnImport}
      />
    );

    fireEvent.click(screen.getByText("Import"));

    expect(mockOnImport).toHaveBeenCalled();
  });

  describe("Scheme details display", () => {
    it("displays scheme details when a scheme is selected", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      // Should show title in details area (not just in list)
      expect(screen.getByTestId("scheme-detail-title")).toHaveTextContent("Animals");
      expect(screen.getByText("http://example.org/animals")).toBeInTheDocument();
      expect(screen.getByText("Animal taxonomy")).toBeInTheDocument();
    });

    it("displays all scheme fields including timestamps", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      // Check that created/updated dates are displayed
      expect(screen.getByText(/created/i)).toBeInTheDocument();
      expect(screen.getByText(/updated/i)).toBeInTheDocument();
    });

    it("handles null/empty optional fields gracefully", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      // Should show labels for optional fields even when null
      expect(screen.getByText(/publisher/i)).toBeInTheDocument();
      expect(screen.getByText(/version/i)).toBeInTheDocument();
    });

    it("does not display scheme details when no scheme is selected", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      // Should not show the detail section
      expect(screen.queryByTestId("scheme-detail-title")).not.toBeInTheDocument();
    });
  });

  describe("Scheme editing", () => {
    it("displays Edit button in read-only mode", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
    });

    it("switches to edit mode when Edit button is clicked", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Should show Cancel and Save buttons instead of Edit
      expect(screen.queryByRole("button", { name: /edit/i })).not.toBeInTheDocument();
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
    });

    it("shows title input field in edit mode", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      expect(titleInput).toBeInTheDocument();
      expect(titleInput.tagName.toLowerCase()).toBe("input");
    });

    it("updates title in draft when input changes", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "Updated Animals" } });

      expect(titleInput).toHaveValue("Updated Animals");
    });

    it("exits edit mode and discards changes when Cancel is clicked", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "Updated Animals" } });

      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

      // Should return to read-only mode with original value
      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      expect(screen.getByTestId("scheme-detail-title")).toHaveTextContent("Animals");
    });

    it("exits edit mode when a different scheme is selected", () => {
      const { rerender } = render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Select different scheme
      rerender(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-2"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      // Should be back in read-only mode
      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /cancel/i })).not.toBeInTheDocument();
    });
  });

  describe("Saving changes", () => {
    beforeEach(() => {
      vi.mocked(schemesApi.update).mockResolvedValue({
        ...mockSchemes[0],
        title: "Updated Title",
      });
    });

    it("displays input fields for all editable properties", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      // Should have inputs for all editable fields
      expect(screen.getByDisplayValue("Animals")).toBeInTheDocument(); // title
      expect(screen.getByDisplayValue("http://example.org/animals")).toBeInTheDocument(); // uri
      expect(screen.getByDisplayValue("Animal taxonomy")).toBeInTheDocument(); // description
      // publisher and version are null, so they should be empty inputs
      expect(screen.getAllByRole("textbox").length).toBeGreaterThanOrEqual(5);
    });

    it("calls API with updated data when Save is clicked", async () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "Updated Animals" } });

      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(schemesApi.update).toHaveBeenCalledWith("scheme-1", {
          title: "Updated Animals",
          uri: "http://example.org/animals",
          description: "Animal taxonomy",
          publisher: null,
          version: null,
        });
      });
    });

    it("exits edit mode after successful save", async () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      });
    });

    it("updates schemes signal after successful save", async () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      const initialSchemesCount = schemes.value.length;

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      });

      // schemes array should still have same count but updated data
      expect(schemes.value.length).toBe(initialSchemesCount);
    });

    it("shows loading state on Save button while saving", async () => {
      vi.mocked(schemesApi.update).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

      // Button should show loading text and be disabled
      await waitFor(() => {
        const saveButton = screen.getByRole("button", { name: /saving/i });
        expect(saveButton).toBeDisabled();
      });
    });
  });

  describe("Validation", () => {
    it("shows error when title is empty", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "" } });

      expect(screen.getByText(/title is required/i)).toBeInTheDocument();
    });

    it("shows error for malformed URI", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const uriInput = screen.getByDisplayValue("http://example.org/animals");
      fireEvent.input(uriInput, { target: { value: "not-a-url" } });

      expect(screen.getByText(/must be a valid url/i)).toBeInTheDocument();
    });

    it("accepts empty URI", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const uriInput = screen.getByDisplayValue("http://example.org/animals");
      fireEvent.input(uriInput, { target: { value: "" } });

      // Should not show any URI validation error for empty value
      expect(screen.queryByText(/must be a valid url/i)).not.toBeInTheDocument();
    });

    it("disables Save button when validation fails", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "" } });

      const saveButton = screen.getByRole("button", { name: /^save$/i });
      expect(saveButton).toBeDisabled();
    });

    it("clears validation error when field is corrected", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "" } });
      expect(screen.getByText(/title is required/i)).toBeInTheDocument();

      fireEvent.input(titleInput, { target: { value: "New Title" } });
      expect(screen.queryByText(/title is required/i)).not.toBeInTheDocument();
    });

    it("allows http and https URIs", () => {
      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));

      const uriInput = screen.getByDisplayValue("http://example.org/animals");

      // Test https
      fireEvent.input(uriInput, { target: { value: "https://example.org/test" } });
      expect(screen.queryByText(/must be a valid url/i)).not.toBeInTheDocument();

      // Test http
      fireEvent.input(uriInput, { target: { value: "http://example.org/test" } });
      expect(screen.queryByText(/must be a valid url/i)).not.toBeInTheDocument();
    });
  });

  describe("Error handling", () => {
    it("displays error message when save fails", async () => {
      const errorMessage = "Network error occurred";
      vi.mocked(schemesApi.update).mockRejectedValue(new Error(errorMessage));

      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      // Should still be in edit mode
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    });

    it("clears error message on retry", async () => {
      const errorMessage = "Network error occurred";
      vi.mocked(schemesApi.update)
        .mockRejectedValueOnce(new Error(errorMessage))
        .mockResolvedValueOnce({ ...mockSchemes[0] });

      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      // Retry save
      fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(screen.queryByText(errorMessage)).not.toBeInTheDocument();
      });
    });

    it("allows editing after save failure", async () => {
      vi.mocked(schemesApi.update).mockRejectedValue(new Error("Save failed"));

      render(
        <SchemesPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
      fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(screen.getByText(/save failed/i)).toBeInTheDocument();
      });

      // Should still be able to edit fields
      const titleInput = screen.getByDisplayValue("Animals");
      fireEvent.input(titleInput, { target: { value: "New Title" } });
      expect(titleInput).toHaveValue("New Title");
    });
  });
});
