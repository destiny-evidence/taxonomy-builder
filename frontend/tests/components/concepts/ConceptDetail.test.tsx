import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/preact";
import { ConceptDetail } from "../../../src/components/concepts/ConceptDetail";
import { concepts } from "../../../src/state/concepts";
import * as conceptsApi from "../../../src/api/concepts";
import type { Concept } from "../../../src/types/models";

// Mock components that have Modal dependencies
vi.mock("../../../src/components/concepts/BroaderSelector", () => ({
  BroaderSelector: () => <div data-testid="broader-selector">BroaderSelector</div>,
}));

vi.mock("../../../src/components/concepts/RelatedSelector", () => ({
  RelatedSelector: () => <div data-testid="related-selector">RelatedSelector</div>,
}));

vi.mock("../../../src/components/common/ConfirmDialog", () => ({
  ConfirmDialog: () => <div data-testid="confirm-dialog">ConfirmDialog</div>,
}));

const mockConcept: Concept = {
  id: "concept-1",
  pref_label: "Test Concept",
  identifier: "001",
  definition: "Test definition",
  scope_note: "Test scope note",
  alt_labels: ["Alternative 1", "Alternative 2"],
  uri: "http://example.org/concepts/001",
  broader: [],
  narrower: [],
  related: [],
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-02T00:00:00Z",
};

describe("ConceptDetail", () => {
  const defaultProps = {
    concept: mockConcept,
    onDelete: vi.fn(),
    onRefresh: vi.fn(),
  };

  beforeEach(() => {
    vi.resetAllMocks();
    concepts.value = [mockConcept];
  });

  describe("edit mode toggle", () => {
    it("should start in read-only mode", () => {
      render(<ConceptDetail {...defaultProps} />);

      expect(screen.getByText("Edit")).toBeInTheDocument();
      expect(screen.queryByText("Cancel")).not.toBeInTheDocument();
      expect(screen.queryByText("Save Changes")).not.toBeInTheDocument();
    });

    it("should toggle to edit mode when Edit button clicked", () => {
      render(<ConceptDetail {...defaultProps} />);

      const editButton = screen.getByText("Edit");
      fireEvent.click(editButton);

      expect(screen.getByText("Cancel")).toBeInTheDocument();
      expect(screen.getByText("Save Changes")).toBeInTheDocument();
      expect(screen.queryByText("Edit")).not.toBeInTheDocument();
    });
  });

  describe("preferred label editing", () => {
    it("should show pref_label as input when editing", () => {
      render(<ConceptDetail {...defaultProps} />);

      const editButton = screen.getByText("Edit");
      fireEvent.click(editButton);

      const input = screen.getByLabelText(/Preferred Label/i) as HTMLInputElement;
      expect(input).toBeInTheDocument();
      expect(input.value).toBe(mockConcept.pref_label);
    });

    it("should update pref_label when typing", () => {
      render(<ConceptDetail {...defaultProps} />);

      const editButton = screen.getByText("Edit");
      fireEvent.click(editButton);

      const input = screen.getByLabelText(/Preferred Label/i) as HTMLInputElement;
      fireEvent.input(input, { target: { value: "New Label" } });

      expect(input.value).toBe("New Label");
    });

    it("should show pref_label as text when not editing", () => {
      render(<ConceptDetail {...defaultProps} />);

      expect(screen.getByText("Test Concept")).toBeInTheDocument();
      expect(screen.queryByLabelText(/Preferred Label/i)).not.toBeInTheDocument();
    });
  });

  describe("all fields editing", () => {
    it("should show all fields as editable in edit mode", () => {
      render(<ConceptDetail {...defaultProps} />);

      const editButton = screen.getByText("Edit");
      fireEvent.click(editButton);

      expect(screen.getByLabelText(/Preferred Label/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Identifier/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Definition/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Scope Note/i)).toBeInTheDocument();
      expect(screen.getByText("Alternative Labels")).toBeInTheDocument();
    });

    it("should initialize fields with concept data", () => {
      render(<ConceptDetail {...defaultProps} />);

      const editButton = screen.getByText("Edit");
      fireEvent.click(editButton);

      expect((screen.getByLabelText(/Preferred Label/i) as HTMLInputElement).value).toBe(mockConcept.pref_label);
      expect((screen.getByLabelText(/Identifier/i) as HTMLInputElement).value).toBe(mockConcept.identifier);
      expect((screen.getByLabelText(/Definition/i) as HTMLTextAreaElement).value).toBe(mockConcept.definition);
      expect((screen.getByLabelText(/Scope Note/i) as HTMLTextAreaElement).value).toBe(mockConcept.scope_note);
    });
  });

  describe("save functionality", () => {
    it("should save changes when Save button clicked", async () => {
      const mockUpdate = vi.fn().mockResolvedValue({ ...mockConcept, pref_label: "Updated" });
      vi.spyOn(conceptsApi.conceptsApi, "update").mockImplementation(mockUpdate);
      const onRefresh = vi.fn();

      render(<ConceptDetail {...defaultProps} onRefresh={onRefresh} />);

      fireEvent.click(screen.getByText("Edit"));
      const input = screen.getByLabelText(/Preferred Label/i) as HTMLInputElement;
      fireEvent.input(input, { target: { value: "Updated" } });
      fireEvent.click(screen.getByText("Save Changes"));

      await waitFor(() => {
        expect(mockUpdate).toHaveBeenCalledWith(mockConcept.id, {
          pref_label: "Updated",
          identifier: mockConcept.identifier,
          definition: mockConcept.definition,
          scope_note: mockConcept.scope_note,
          alt_labels: mockConcept.alt_labels,
        });
        expect(onRefresh).toHaveBeenCalled();
      });
    });

    it("should exit edit mode after successful save", async () => {
      vi.spyOn(conceptsApi.conceptsApi, "update").mockResolvedValue(mockConcept);
      const onRefresh = vi.fn();

      render(<ConceptDetail {...defaultProps} onRefresh={onRefresh} />);

      fireEvent.click(screen.getByText("Edit"));
      fireEvent.click(screen.getByText("Save Changes"));

      await waitFor(() => {
        expect(screen.getByText("Edit")).toBeInTheDocument();
        expect(screen.queryByText("Save Changes")).not.toBeInTheDocument();
      });
    });

    it("should show error message when save fails", async () => {
      vi.spyOn(conceptsApi.conceptsApi, "update").mockRejectedValue(new Error("Save failed"));

      render(<ConceptDetail {...defaultProps} />);

      fireEvent.click(screen.getByText("Edit"));
      fireEvent.click(screen.getByText("Save Changes"));

      await waitFor(() => {
        expect(screen.getByText(/Save failed/)).toBeInTheDocument();
      });
    });

    it("should show loading state while saving", async () => {
      let resolveUpdate: (value: any) => void;
      const updatePromise = new Promise((resolve) => {
        resolveUpdate = resolve;
      });
      vi.spyOn(conceptsApi.conceptsApi, "update").mockReturnValue(updatePromise as any);

      render(<ConceptDetail {...defaultProps} />);

      fireEvent.click(screen.getByText("Edit"));
      fireEvent.click(screen.getByText("Save Changes"));

      expect(screen.getByText("Saving...")).toBeInTheDocument();
      expect(screen.getByText("Saving...")).toBeDisabled();

      resolveUpdate!(mockConcept);
    });
  });

  describe("cancel functionality", () => {
    it("should discard changes when Cancel button clicked", () => {
      render(<ConceptDetail {...defaultProps} />);

      fireEvent.click(screen.getByText("Edit"));
      const input = screen.getByLabelText(/Preferred Label/i) as HTMLInputElement;
      fireEvent.input(input, { target: { value: "Changed" } });
      fireEvent.click(screen.getByText("Cancel"));

      // Should exit edit mode
      expect(screen.queryByText("Cancel")).not.toBeInTheDocument();
      expect(screen.getByText("Edit")).toBeInTheDocument();
      // Original value should be displayed
      expect(screen.getByText("Test Concept")).toBeInTheDocument();
    });

    it("should exit edit mode when concept changes", () => {
      const newConcept: Concept = { ...mockConcept, id: "concept-2", pref_label: "Different Concept" };
      const { rerender } = render(<ConceptDetail {...defaultProps} />);

      fireEvent.click(screen.getByText("Edit"));
      expect(screen.getByText("Cancel")).toBeInTheDocument();

      // Simulate selecting different concept
      rerender(<ConceptDetail {...defaultProps} concept={newConcept} />);

      // Should exit edit mode
      expect(screen.queryByText("Cancel")).not.toBeInTheDocument();
      expect(screen.getByText("Edit")).toBeInTheDocument();
    });

    it("should reset fields to original values when canceled", () => {
      render(<ConceptDetail {...defaultProps} />);

      fireEvent.click(screen.getByText("Edit"));

      const prefLabelInput = screen.getByLabelText(/Preferred Label/i) as HTMLInputElement;
      const identifierInput = screen.getByLabelText(/Identifier/i) as HTMLInputElement;

      fireEvent.input(prefLabelInput, { target: { value: "Changed Label" } });
      fireEvent.input(identifierInput, { target: { value: "changed-id" } });

      fireEvent.click(screen.getByText("Cancel"));
      fireEvent.click(screen.getByText("Edit"));

      // Fields should be back to original values
      expect((screen.getByLabelText(/Preferred Label/i) as HTMLInputElement).value).toBe(mockConcept.pref_label);
      expect((screen.getByLabelText(/Identifier/i) as HTMLInputElement).value).toBe(mockConcept.identifier);
    });
  });
});
