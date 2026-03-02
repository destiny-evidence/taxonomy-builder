import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { ProjectPane } from "../../../src/components/workspace/ProjectPane";
import { currentProject } from "../../../src/state/projects";
import { schemes } from "../../../src/state/schemes";
import { selectedClassUri } from "../../../src/state/classes";
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
vi.mock("../../../src/state/classes", async () => {
  const actual = await vi.importActual("../../../src/state/classes");
  return {
    ...actual,
    ontologyClasses: {
      value: [
        { id: "cls-1", project_id: "proj-1", identifier: "Investigation", uri: "http://example.org/Investigation", label: "Investigation", description: "A research effort", scope_note: null, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
        { id: "cls-2", project_id: "proj-1", identifier: "Finding", uri: "http://example.org/Finding", label: "Finding", description: "A specific result", scope_note: null, created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-02T00:00:00Z" },
      ],
    },
  };
});

function renderPane(overrides: Partial<Parameters<typeof ProjectPane>[0]> = {}) {
  const defaults = {
    projectId: "proj-1",
    currentSchemeId: null as string | null,
    onSchemeSelect: vi.fn(),
    onClassSelect: vi.fn(),
    onNewClass: vi.fn(),
    onNewScheme: vi.fn(),
    onImport: vi.fn(),
    onPublish: vi.fn(),
    onVersions: vi.fn(),
  };
  const props = { ...defaults, ...overrides };
  return { ...render(<ProjectPane {...props} />), props };
}

describe("ProjectPane", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    currentProject.value = mockProject;
    schemes.value = mockSchemes;
    selectionMode.value = null;
    selectedClassUri.value = null;
  });

  describe("header", () => {
    it("renders project name", () => {
      renderPane();
      expect(screen.getByText("Test Project")).toBeInTheDocument();
    });

    it("renders back link to projects", () => {
      renderPane();
      const backLink = screen.getByRole("link", { name: /projects/i });
      expect(backLink).toHaveAttribute("href", "/projects");
    });
  });

  describe("publish button", () => {
    it("shows New version button", () => {
      const { props } = renderPane();
      const btn = screen.getByRole("button", { name: "New Version" });
      expect(btn).toBeInTheDocument();

      fireEvent.click(btn);
      expect(props.onPublish).toHaveBeenCalled();
    });

    it("has a History button that calls onVersions", () => {
      const { props } = renderPane();
      const btn = screen.getByRole("button", { name: "History" });
      expect(btn).toBeInTheDocument();

      fireEvent.click(btn);
      expect(props.onVersions).toHaveBeenCalled();
    });
  });

  describe("classes section", () => {
    it("lists ontology classes", () => {
      renderPane();
      expect(screen.getByText("Investigation")).toBeInTheDocument();
      expect(screen.getByText("Finding")).toBeInTheDocument();
    });

    it("calls onClassSelect when class is clicked", () => {
      const { props } = renderPane();
      fireEvent.click(screen.getByText("Investigation"));
      expect(props.onClassSelect).toHaveBeenCalledWith("http://example.org/Investigation");
    });

    it("calls onNewClass when New Class button clicked", () => {
      const { props } = renderPane();
      fireEvent.click(screen.getByText("+ New Class"));
      expect(props.onNewClass).toHaveBeenCalled();
    });

    it("highlights selected class", () => {
      selectedClassUri.value = "http://example.org/Investigation";
      selectionMode.value = "class";

      renderPane();
      const classButton = screen.getByRole("button", { name: "Investigation" });
      expect(classButton).toHaveClass("project-pane__item--selected");
    });
  });

  describe("schemes section", () => {
    it("lists schemes for the project", () => {
      renderPane();
      expect(screen.getByText("Countries")).toBeInTheDocument();
      expect(screen.getByText("Languages")).toBeInTheDocument();
    });

    it("calls onSchemeSelect when scheme is clicked", () => {
      const { props } = renderPane();
      fireEvent.click(screen.getByText("Countries"));
      expect(props.onSchemeSelect).toHaveBeenCalledWith("scheme-1");
    });

    it("highlights current scheme", () => {
      selectionMode.value = "scheme";
      renderPane({ currentSchemeId: "scheme-1" });
      const schemeButton = screen.getByRole("button", { name: "Countries" });
      expect(schemeButton).toHaveClass("project-pane__item--selected");
    });

    it("shows empty state when no schemes", () => {
      schemes.value = [];
      renderPane();
      expect(screen.getByText(/no schemes/i)).toBeInTheDocument();
    });

    it("calls onNewScheme when New Scheme button clicked", () => {
      const { props } = renderPane();
      fireEvent.click(screen.getByText("+ New Scheme"));
      expect(props.onNewScheme).toHaveBeenCalled();
    });

    it("calls onImport when Import button clicked", () => {
      const { props } = renderPane();
      fireEvent.click(screen.getByText("Import"));
      expect(props.onImport).toHaveBeenCalled();
    });
  });
});
