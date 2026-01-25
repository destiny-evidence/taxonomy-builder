import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { ConceptDetail } from "../../../src/components/concepts/ConceptDetail";
import { concepts } from "../../../src/state/concepts";
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
    onEdit: vi.fn(),
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

    it("should not call onEdit when Edit button clicked", () => {
      const onEdit = vi.fn();
      render(<ConceptDetail {...defaultProps} onEdit={onEdit} />);

      const editButton = screen.getByText("Edit");
      fireEvent.click(editButton);

      // onEdit should not be called because we're handling edit mode internally now
      expect(onEdit).not.toHaveBeenCalled();
    });
  });
});
