import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { SchemesPane } from "../../../src/components/workspace/SchemesPane";
import { projects } from "../../../src/state/projects";
import { schemes } from "../../../src/state/schemes";
import type { Project, ConceptScheme } from "../../../src/types/models";

const mockProjects: Project[] = [
  {
    id: "proj-1",
    name: "Project One",
    description: "First project",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "proj-2",
    name: "Project Two",
    description: "Second project",
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

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
  const mockOnProjectChange = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
    projects.value = mockProjects;
    schemes.value = mockSchemes;
  });

  it("renders current project name in dropdown", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onProjectChange={mockOnProjectChange}
      />
    );

    expect(screen.getByText("Project One")).toBeInTheDocument();
  });

  it("lists schemes for the current project", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onProjectChange={mockOnProjectChange}
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
        onProjectChange={mockOnProjectChange}
      />
    );

    const animalsItem = screen.getByText("Animals").closest("button");
    expect(animalsItem).toHaveClass("schemes-pane__item--selected");
  });

  it("calls onSchemeSelect when scheme is clicked", () => {
    render(
      <SchemesPane
        projectId="proj-1"
        currentSchemeId={null}
        onSchemeSelect={mockOnSchemeSelect}
        onProjectChange={mockOnProjectChange}
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
        onProjectChange={mockOnProjectChange}
      />
    );

    expect(screen.getByText(/no schemes/i)).toBeInTheDocument();
  });
});
