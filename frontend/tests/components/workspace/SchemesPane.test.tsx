import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { SchemesPane } from "../../../src/components/workspace/SchemesPane";
import { currentProject } from "../../../src/state/projects";
import { schemes } from "../../../src/state/schemes";
import type { Project, ConceptScheme } from "../../../src/types/models";

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
});
