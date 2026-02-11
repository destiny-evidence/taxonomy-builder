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
  namespace: null,
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
  const mockOnPropertiesSelect = vi.fn();
  const mockOnNewScheme = vi.fn();
  const mockOnImport = vi.fn();

  const defaultProps = {
    projectId: "proj-1",
    currentSchemeId: null as string | null,
    showProperties: false,
    onSchemeSelect: mockOnSchemeSelect,
    onPropertiesSelect: mockOnPropertiesSelect,
    onNewScheme: mockOnNewScheme,
    onImport: mockOnImport,
  };

  beforeEach(() => {
    vi.resetAllMocks();
    currentProject.value = mockProject;
    schemes.value = mockSchemes;
  });

  it("renders current project name as heading", () => {
    render(<SchemesPane {...defaultProps} />);

    expect(screen.getByText("Project One")).toBeInTheDocument();
  });

  it("renders back link to projects", () => {
    render(<SchemesPane {...defaultProps} />);

    const backLink = screen.getByRole("link", { name: /projects/i });
    expect(backLink).toHaveAttribute("href", "/projects");
  });

  it("lists schemes for the current project", () => {
    render(<SchemesPane {...defaultProps} />);

    expect(screen.getByText("Animals")).toBeInTheDocument();
    expect(screen.getByText("Plants")).toBeInTheDocument();
  });

  it("highlights the current scheme", () => {
    render(<SchemesPane {...defaultProps} currentSchemeId="scheme-1" />);

    const schemeList = screen.getByRole("button", { name: "Animals" });
    expect(schemeList).toHaveClass("schemes-pane__item--selected");
  });

  it("calls onSchemeSelect when scheme is clicked", () => {
    render(<SchemesPane {...defaultProps} />);

    fireEvent.click(screen.getByText("Animals"));

    expect(mockOnSchemeSelect).toHaveBeenCalledWith("scheme-1");
  });

  it("shows empty state when project has no schemes", () => {
    schemes.value = [];

    render(<SchemesPane {...defaultProps} />);

    expect(screen.getByText(/no schemes/i)).toBeInTheDocument();
  });

  it("calls onNewScheme when New Scheme button is clicked", () => {
    render(<SchemesPane {...defaultProps} />);

    fireEvent.click(screen.getByText("+ New Scheme"));

    expect(mockOnNewScheme).toHaveBeenCalled();
  });

  it("calls onImport when Import button is clicked", () => {
    render(<SchemesPane {...defaultProps} />);

    fireEvent.click(screen.getByText("Import"));

    expect(mockOnImport).toHaveBeenCalled();
  });

  it("renders Properties nav item", () => {
    render(<SchemesPane {...defaultProps} />);

    expect(screen.getByRole("button", { name: "Properties" })).toBeInTheDocument();
  });

  it("calls onPropertiesSelect when Properties is clicked", () => {
    render(<SchemesPane {...defaultProps} />);

    fireEvent.click(screen.getByRole("button", { name: "Properties" }));

    expect(mockOnPropertiesSelect).toHaveBeenCalled();
  });

  it("highlights Properties when showProperties is true", () => {
    render(<SchemesPane {...defaultProps} showProperties={true} />);

    const propertiesBtn = screen.getByRole("button", { name: "Properties" });
    expect(propertiesBtn).toHaveClass("schemes-pane__item--selected");
  });

  it("does not highlight Properties when a scheme is selected", () => {
    render(
      <SchemesPane {...defaultProps} currentSchemeId="scheme-1" showProperties={false} />
    );

    const propertiesBtn = screen.getByRole("button", { name: "Properties" });
    expect(propertiesBtn).not.toHaveClass("schemes-pane__item--selected");
  });
});
