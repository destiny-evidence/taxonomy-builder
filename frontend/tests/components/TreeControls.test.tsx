import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { TreeControls } from "../../src/components/tree/TreeControls";
import { searchQuery, hideNonMatches } from "../../src/state/search";

const defaultProps = {
  onExpandAll: vi.fn(),
  onCollapseAll: vi.fn(),
};

describe("TreeControls", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    searchQuery.value = "";
    hideNonMatches.value = false;
  });

  describe("expand/collapse buttons", () => {
    it("renders Expand All button", () => {
      render(<TreeControls {...defaultProps} />);
      expect(screen.getByText("Expand All")).toBeInTheDocument();
    });

    it("renders Collapse All button", () => {
      render(<TreeControls {...defaultProps} />);
      expect(screen.getByText("Collapse All")).toBeInTheDocument();
    });

    it("calls onExpandAll when Expand All is clicked", () => {
      render(<TreeControls {...defaultProps} />);
      fireEvent.click(screen.getByText("Expand All"));
      expect(defaultProps.onExpandAll).toHaveBeenCalled();
    });

    it("calls onCollapseAll when Collapse All is clicked", () => {
      render(<TreeControls {...defaultProps} />);
      fireEvent.click(screen.getByText("Collapse All"));
      expect(defaultProps.onCollapseAll).toHaveBeenCalled();
    });
  });

  describe("search input", () => {
    it("renders search input with placeholder", () => {
      render(<TreeControls {...defaultProps} />);
      expect(screen.getByPlaceholderText("Search concepts...")).toBeInTheDocument();
    });

    it("updates searchQuery signal when typing", () => {
      render(<TreeControls {...defaultProps} />);
      const input = screen.getByPlaceholderText("Search concepts...");
      fireEvent.input(input, { target: { value: "dogs" } });
      expect(searchQuery.value).toBe("dogs");
    });

    it("shows clear button when query is non-empty", () => {
      searchQuery.value = "dogs";
      render(<TreeControls {...defaultProps} />);
      expect(screen.getByLabelText("Clear search")).toBeInTheDocument();
    });

    it("hides clear button when query is empty", () => {
      searchQuery.value = "";
      render(<TreeControls {...defaultProps} />);
      expect(screen.queryByLabelText("Clear search")).not.toBeInTheDocument();
    });

    it("clears searchQuery when clear button is clicked", () => {
      searchQuery.value = "dogs";
      render(<TreeControls {...defaultProps} />);
      fireEvent.click(screen.getByLabelText("Clear search"));
      expect(searchQuery.value).toBe("");
    });
  });

  describe("hide non-matches checkbox", () => {
    it("is not visible when search query is empty", () => {
      searchQuery.value = "";
      render(<TreeControls {...defaultProps} />);
      expect(screen.queryByLabelText("Hide non-matches")).not.toBeInTheDocument();
    });

    it("is visible when search query is non-empty", () => {
      searchQuery.value = "dogs";
      render(<TreeControls {...defaultProps} />);
      expect(screen.getByLabelText("Hide non-matches")).toBeInTheDocument();
    });

    it("is unchecked by default", () => {
      searchQuery.value = "dogs";
      render(<TreeControls {...defaultProps} />);
      const checkbox = screen.getByLabelText("Hide non-matches") as HTMLInputElement;
      expect(checkbox.checked).toBe(false);
    });

    it("updates hideNonMatches signal when toggled", () => {
      searchQuery.value = "dogs";
      render(<TreeControls {...defaultProps} />);
      const checkbox = screen.getByLabelText("Hide non-matches");
      fireEvent.click(checkbox);
      expect(hideNonMatches.value).toBe(true);
    });
  });
});
