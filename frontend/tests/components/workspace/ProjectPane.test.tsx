import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { ProjectPane } from "../../../src/components/workspace/ProjectPane";
import { currentProject } from "../../../src/state/projects";
import { schemes } from "../../../src/state/schemes";
import { selectedClassUri } from "../../../src/state/ontology";
import { selectionMode } from "../../../src/state/workspace";
import type { Project, ConceptScheme } from "../../../src/types/models";

const mockProject: Project = {
  id: "proj-1",
  name: "Test Project",
  description: "A test project",
  namespace: null,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockSchemes: ConceptScheme[] = [
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
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

// Mock the ontologyClasses computed signal
vi.mock("../../../src/state/ontology", async () => {
  const actual = await vi.importActual("../../../src/state/ontology");
  return {
    ...actual,
    ontologyClasses: {
      value: [
        { uri: "http://example.org/Investigation", label: "Investigation", comment: "A research effort" },
        { uri: "http://example.org/Finding", label: "Finding", comment: "A specific result" },
      ],
    },
  };
});

describe("ProjectPane", () => {
  const mockOnSchemeSelect = vi.fn();
  const mockOnClassSelect = vi.fn();
  const mockOnNewScheme = vi.fn();
  const mockOnImport = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    currentProject.value = mockProject;
    schemes.value = mockSchemes;
    selectionMode.value = null;
    selectedClassUri.value = null;
  });

  describe("header", () => {
    it("renders project name", () => {
      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText("Test Project")).toBeInTheDocument();
    });

    it("renders back link to projects", () => {
      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      const backLink = screen.getByRole("link", { name: /projects/i });
      expect(backLink).toHaveAttribute("href", "/projects");
    });
  });

  describe("classes section", () => {
    it("lists ontology classes", () => {
      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText("Investigation")).toBeInTheDocument();
      expect(screen.getByText("Finding")).toBeInTheDocument();
    });

    it("calls onClassSelect when class is clicked", () => {
      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByText("Investigation"));

      expect(mockOnClassSelect).toHaveBeenCalledWith("http://example.org/Investigation");
    });

    it("highlights selected class", () => {
      selectedClassUri.value = "http://example.org/Investigation";
      selectionMode.value = "class";

      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      const classButton = screen.getByRole("button", { name: "Investigation" });
      expect(classButton).toHaveClass("project-pane__item--selected");
    });
  });

  describe("schemes section", () => {
    it("lists schemes for the project", () => {
      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText("Countries")).toBeInTheDocument();
      expect(screen.getByText("Languages")).toBeInTheDocument();
    });

    it("calls onSchemeSelect when scheme is clicked", () => {
      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByText("Countries"));

      expect(mockOnSchemeSelect).toHaveBeenCalledWith("scheme-1");
    });

    it("highlights current scheme", () => {
      selectionMode.value = "scheme";

      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId="scheme-1"
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      const schemeButton = screen.getByRole("button", { name: "Countries" });
      expect(schemeButton).toHaveClass("project-pane__item--selected");
    });

    it("shows empty state when no schemes", () => {
      schemes.value = [];

      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText(/no schemes/i)).toBeInTheDocument();
    });

    it("calls onNewScheme when New Scheme button clicked", () => {
      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByText("+ New Scheme"));

      expect(mockOnNewScheme).toHaveBeenCalled();
    });

    it("calls onImport when Import button clicked", () => {
      render(
        <ProjectPane
          projectId="proj-1"
          currentSchemeId={null}
          onSchemeSelect={mockOnSchemeSelect}
          onClassSelect={mockOnClassSelect}
          onNewScheme={mockOnNewScheme}
          onImport={mockOnImport}
        />
      );

      fireEvent.click(screen.getByText("Import"));

      expect(mockOnImport).toHaveBeenCalled();
    });
  });
});
