import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { ConceptForm } from "../../../src/components/concepts/ConceptForm";

describe("ConceptForm", () => {
  const defaultProps = {
    schemeId: "scheme-123",
    onSuccess: vi.fn(),
    onCancel: vi.fn(),
  };

  describe("URI computation", () => {
    it("shows computed URI with scheme URI and identifier", () => {
      render(
        <ConceptForm
          {...defaultProps}
          schemeUri="http://example.org/vocab"
        />
      );

      const identifierInput = screen.getByLabelText(/Identifier/);
      fireEvent.input(identifierInput, { target: { value: "animals" } });

      expect(screen.getByText("http://example.org/vocab/animals")).toBeInTheDocument();
    });

    it("uses default base URI when scheme URI not provided", () => {
      render(<ConceptForm {...defaultProps} schemeUri={null} />);

      const identifierInput = screen.getByLabelText(/Identifier/);
      fireEvent.input(identifierInput, { target: { value: "concept-1" } });

      expect(screen.getByText("http://example.org/concepts/concept-1")).toBeInTheDocument();
    });

    it("strips trailing slash from scheme URI", () => {
      render(
        <ConceptForm
          {...defaultProps}
          schemeUri="http://example.org/vocab/"
        />
      );

      const identifierInput = screen.getByLabelText(/Identifier/);
      fireEvent.input(identifierInput, { target: { value: "term" } });

      // Should not double the slash
      expect(screen.getByText("http://example.org/vocab/term")).toBeInTheDocument();
    });

    it("does not show URI preview when identifier is empty", () => {
      render(
        <ConceptForm
          {...defaultProps}
          schemeUri="http://example.org/vocab"
        />
      );

      expect(screen.queryByText(/URI \(computed\)/)).not.toBeInTheDocument();
    });
  });

  describe("form modes", () => {
    it("shows 'Create Concept' button in create mode", () => {
      render(<ConceptForm {...defaultProps} />);

      expect(screen.getByText("Create Concept")).toBeInTheDocument();
    });

    it("shows 'Save Changes' button in edit mode", () => {
      const existingConcept = {
        id: "c-1",
        scheme_id: "scheme-123",
        identifier: "existing",
        pref_label: "Existing Concept",
        definition: null,
        scope_note: null,
        uri: null,
        alt_labels: [],
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        broader: [],
        related: [],
      };

      render(<ConceptForm {...defaultProps} concept={existingConcept} />);

      expect(screen.getByText("Save Changes")).toBeInTheDocument();
    });

    it("populates form fields from existing concept", () => {
      const existingConcept = {
        id: "c-1",
        scheme_id: "scheme-123",
        identifier: "my-id",
        pref_label: "My Label",
        definition: "My definition",
        scope_note: "My scope note",
        uri: null,
        alt_labels: [],
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        broader: [],
        related: [],
      };

      render(<ConceptForm {...defaultProps} concept={existingConcept} />);

      expect(screen.getByDisplayValue("My Label")).toBeInTheDocument();
      expect(screen.getByDisplayValue("my-id")).toBeInTheDocument();
      expect(screen.getByDisplayValue("My definition")).toBeInTheDocument();
      expect(screen.getByDisplayValue("My scope note")).toBeInTheDocument();
    });
  });

  describe("validation", () => {
    it("disables submit when preferred label is empty", () => {
      render(<ConceptForm {...defaultProps} />);

      const submitButton = screen.getByText("Create Concept");
      expect(submitButton).toBeDisabled();
    });

    it("enables submit when preferred label has value", () => {
      render(<ConceptForm {...defaultProps} />);

      const labelInput = screen.getByLabelText(/Preferred Label/);
      fireEvent.input(labelInput, { target: { value: "My Concept" } });

      const submitButton = screen.getByText("Create Concept");
      expect(submitButton).not.toBeDisabled();
    });

    it("disables submit when preferred label is only whitespace", () => {
      render(<ConceptForm {...defaultProps} />);

      const labelInput = screen.getByLabelText(/Preferred Label/);
      fireEvent.input(labelInput, { target: { value: "   " } });

      const submitButton = screen.getByText("Create Concept");
      expect(submitButton).toBeDisabled();
    });
  });

  describe("actions", () => {
    it("calls onCancel when cancel button clicked", () => {
      const onCancel = vi.fn();

      render(<ConceptForm {...defaultProps} onCancel={onCancel} />);

      const cancelButton = screen.getByText("Cancel");
      fireEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalled();
    });
  });
});
