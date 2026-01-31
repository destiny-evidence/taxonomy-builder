import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { ProjectForm } from "../../../src/components/projects/ProjectForm";

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
        namespace: null,
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
        namespace: null,
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

    it("enables submit when name has value", () => {
      render(<ProjectForm {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText("Enter project name");
      fireEvent.input(nameInput, { target: { value: "New Project" } });

      const submitButton = screen.getByText("Create Project");
      expect(submitButton).not.toBeDisabled();
    });

    it("disables submit when name is only whitespace", () => {
      render(<ProjectForm {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText("Enter project name");
      fireEvent.input(nameInput, { target: { value: "   " } });

      const submitButton = screen.getByText("Create Project");
      expect(submitButton).toBeDisabled();
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
