import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { ProjectForm } from "../../../src/components/projects/ProjectForm";
import { projectsApi } from "../../../src/api/projects";

vi.mock("../../../src/api/projects");

describe("ProjectForm", () => {
  const defaultProps = {
    onSuccess: vi.fn(),
    onCancel: vi.fn(),
  };

  describe("form modes", () => {
    it("shows 'Create Project' button in create mode", () => {
      render(<ProjectForm {...defaultProps} />);

      expect(screen.getByText("Create Project")).toBeInTheDocument();
    });

    it("shows 'Save Changes' button in edit mode", () => {
      const existingProject = {
        id: "p-1",
        name: "Existing Project",
        description: "Some description",
        namespace: "https://example.org/vocab",
        identifier_prefix: "EVD",
        identifier_counter: 0,
        prefix_locked: false,
        namespace_prefixes: {},
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      };

      render(<ProjectForm {...defaultProps} project={existingProject} />);

      expect(screen.getByText("Save Changes")).toBeInTheDocument();
    });

    it("populates form fields from existing project", () => {
      const existingProject = {
        id: "p-1",
        name: "My Project",
        description: "Project description",
        namespace: "https://example.org/vocab",
        identifier_prefix: "EVD",
        identifier_counter: 0,
        prefix_locked: false,
        namespace_prefixes: {},
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      };

      render(<ProjectForm {...defaultProps} project={existingProject} />);

      expect(screen.getByDisplayValue("My Project")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Project description")).toBeInTheDocument();
    });
  });

  describe("validation", () => {
    it("disables submit when name is empty", () => {
      render(<ProjectForm {...defaultProps} />);

      const submitButton = screen.getByText("Create Project");
      expect(submitButton).toBeDisabled();
    });

    it("enables submit when name, namespace, and prefix have values", () => {
      render(<ProjectForm {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText("Enter project name");
      fireEvent.input(nameInput, { target: { value: "New Project" } });

      const namespaceInput = screen.getByPlaceholderText("https://example.org/vocab");
      fireEvent.input(namespaceInput, { target: { value: "https://example.org/test" } });

      const prefixInput = screen.getByLabelText(/Identifier Prefix/);
      fireEvent.input(prefixInput, { target: { value: "EVD" } });

      const submitButton = screen.getByText("Create Project");
      expect(submitButton).not.toBeDisabled();
    });

    it("disables submit when namespace is empty", () => {
      render(<ProjectForm {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText("Enter project name");
      fireEvent.input(nameInput, { target: { value: "New Project" } });

      const submitButton = screen.getByText("Create Project");
      expect(submitButton).toBeDisabled();
    });

    it("shows error and disables submit when namespace ends with '#'", () => {
      render(<ProjectForm {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText("Enter project name");
      fireEvent.input(nameInput, { target: { value: "New Project" } });

      const namespaceInput = screen.getByPlaceholderText("https://example.org/vocab");
      fireEvent.input(namespaceInput, { target: { value: "https://example.org/vocab#" } });

      const prefixInput = screen.getByLabelText(/Identifier Prefix/);
      fireEvent.input(prefixInput, { target: { value: "EVD" } });

      expect(screen.getByText("Namespace cannot end with '#'")).toBeInTheDocument();
      expect(screen.getByText("Create Project")).toBeDisabled();
    });

    it("disables submit when name is only whitespace", () => {
      render(<ProjectForm {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText("Enter project name");
      fireEvent.input(nameInput, { target: { value: "   " } });

      const submitButton = screen.getByText("Create Project");
      expect(submitButton).toBeDisabled();
    });
  });

  describe("identifier prefix", () => {
    it("shows required prefix input in create mode", () => {
      render(<ProjectForm {...defaultProps} />);

      const prefixInput = screen.getByLabelText(/Identifier Prefix/);
      expect(prefixInput).toBeInTheDocument();
      expect(prefixInput).toBeRequired();
    });

    it("shows help text for prefix", () => {
      render(<ProjectForm {...defaultProps} />);

      expect(screen.getByText(/1-4 uppercase letters/)).toBeInTheDocument();
    });

    it("shows editable prefix input when prefix is unlocked", () => {
      const project = {
        id: "p-1",
        name: "Test",
        description: null,
        namespace: "https://example.org/vocab",
        identifier_prefix: "EVD",
        identifier_counter: 0,
        prefix_locked: false,
        namespace_prefixes: {},
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      };

      render(<ProjectForm {...defaultProps} project={project} />);

      const prefixInput = screen.getByLabelText(/Identifier Prefix/);
      expect(prefixInput).toHaveValue("EVD");
      expect(prefixInput).not.toBeDisabled();
    });

    it("shows locked prefix badge when prefix_locked is true", () => {
      const project = {
        id: "p-1",
        name: "Test",
        description: null,
        namespace: "https://example.org/vocab",
        identifier_prefix: "EVD",
        identifier_counter: 5,
        prefix_locked: true,
        namespace_prefixes: {},
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      };

      render(<ProjectForm {...defaultProps} project={project} />);

      expect(screen.getByText("EVD")).toBeInTheDocument();
      expect(screen.getByText(/Locked — identifiers in use/)).toBeInTheDocument();
      expect(screen.queryByLabelText(/Identifier Prefix/)).not.toBeInTheDocument();
    });

    it("disables submit when prefix is empty in create mode", () => {
      render(<ProjectForm {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText("Enter project name");
      fireEvent.input(nameInput, { target: { value: "New Project" } });

      const namespaceInput = screen.getByPlaceholderText("https://example.org/vocab");
      fireEvent.input(namespaceInput, { target: { value: "https://example.org/test" } });

      // Don't fill prefix
      const submitButton = screen.getByText("Create Project");
      expect(submitButton).toBeDisabled();
    });

    it("enables submit when name, namespace, and prefix all have values", () => {
      render(<ProjectForm {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText("Enter project name");
      fireEvent.input(nameInput, { target: { value: "New Project" } });

      const namespaceInput = screen.getByPlaceholderText("https://example.org/vocab");
      fireEvent.input(namespaceInput, { target: { value: "https://example.org/test" } });

      const prefixInput = screen.getByLabelText(/Identifier Prefix/);
      fireEvent.input(prefixInput, { target: { value: "EVD" } });

      const submitButton = screen.getByText("Create Project");
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe("namespace", () => {
    const existingProject = {
      id: "p-1",
      name: "Test",
      description: null,
      namespace: "https://example.org/vocab",
      identifier_prefix: "EVD",
      identifier_counter: 0,
      prefix_locked: false,
      namespace_prefixes: {},
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    };

    it("is editable with help text in create mode", () => {
      render(<ProjectForm {...defaultProps} />);

      expect(screen.getByLabelText(/Namespace/)).not.toBeDisabled();
      expect(screen.getByText(/Cannot be changed after the project is created/)).toBeInTheDocument();
    });

    it("is shown as read-only text in edit mode", () => {
      render(<ProjectForm {...defaultProps} project={existingProject} />);

      expect(screen.getByText("https://example.org/vocab")).toBeInTheDocument();
      expect(screen.queryByLabelText(/Namespace/)).not.toBeInTheDocument();
    });

    it("is not sent when updating a project", async () => {
      render(<ProjectForm {...defaultProps} project={existingProject} />);

      fireEvent.click(screen.getByText("Save Changes"));

      await waitFor(() => expect(projectsApi.update).toHaveBeenCalled());
      expect(vi.mocked(projectsApi.update).mock.calls[0][1]).not.toHaveProperty("namespace");
    });
  });

  describe("actions", () => {
    it("calls onCancel when cancel button clicked", () => {
      const onCancel = vi.fn();

      render(<ProjectForm {...defaultProps} onCancel={onCancel} />);

      const cancelButton = screen.getByText("Cancel");
      fireEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalled();
    });
  });
});
