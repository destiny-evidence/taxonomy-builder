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

function renderPane(overrides: Partial<Parameters<typeof ProjectPane>[0]> = {}) {
  const defaults = {
    projectId: "proj-1",
    currentSchemeId: null as string | null,
    onSchemeSelect: vi.fn(),
    onClassSelect: vi.fn(),
    onNewScheme: vi.fn(),
    onImport: vi.fn(),
    onPublish: vi.fn(),
    onVersions: vi.fn(),
    draft: null as { version: string; title: string } | null,
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
    it("shows Publish when no draft exists", () => {
      const { props } = renderPane();
      const btn = screen.getByRole("button", { name: "Publish" });
      expect(btn).toBeInTheDocument();

      fireEvent.click(btn);
      expect(props.onPublish).toHaveBeenCalled();
    });

    it("shows drafting state when draft exists", () => {
      renderPane({ draft: { version: "1.2", title: "Beta release" } });
      expect(screen.getByText(/Drafting v1\.2/)).toBeInTheDocument();
    });

    it("applies draft styling when draft exists", () => {
      renderPane({ draft: { version: "1.0", title: "Initial" } });
      const btn = screen.getByRole("button", { name: /drafting/i });
      expect(btn.closest(".project-pane__publish-group")).toHaveClass("project-pane__publish-group--draft");
    });

    it("calls onPublish when draft button clicked", () => {
      const { props } = renderPane({ draft: { version: "2.0", title: "Next" } });
      fireEvent.click(screen.getByRole("button", { name: /drafting/i }));
      expect(props.onPublish).toHaveBeenCalled();
    });

    it("has a versions button that calls onVersions", () => {
      const { props } = renderPane();
      const btn = screen.getByRole("button", { name: /version history/i });
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
