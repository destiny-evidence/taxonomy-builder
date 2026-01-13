import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { DndContext } from "@dnd-kit/core";
import { TreeNode } from "../../../src/components/tree/TreeNode";
import { draggedConceptId } from "../../../src/state/concepts";
import { searchQuery } from "../../../src/state/search";
import type { RenderNode } from "../../../src/types/models";

describe("TreeNode", () => {
  function createNode(overrides: Partial<RenderNode> = {}): RenderNode {
    return {
      id: "node-1",
      pref_label: "Test Node",
      definition: null,
      path: "node-1",
      depth: 0,
      hasMultipleParents: false,
      otherParentLabels: [],
      children: [],
      matchStatus: "none",
      ...overrides,
    };
  }

  const defaultProps = {
    expandedPaths: new Set<string>(),
    selectedId: null,
    onToggle: vi.fn(),
    onSelect: vi.fn(),
  };

  // Helper to render TreeNode wrapped in DndContext
  function renderWithDnd(ui: preact.JSX.Element) {
    return render(<DndContext>{ui}</DndContext>);
  }

  beforeEach(() => {
    draggedConceptId.value = null;
    searchQuery.value = "";
  });

  describe("toggle button", () => {
    it("shows toggle button when node has children", () => {
      const node = createNode({
        children: [createNode({ id: "child-1", pref_label: "Child" })],
      });

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      expect(screen.getByRole("button", { name: /Expand/i })).toBeInTheDocument();
    });

    it("does not show toggle button when node has no children", () => {
      const node = createNode({ children: [] });

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      expect(screen.queryByRole("button", { name: /Expand/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /Collapse/i })).not.toBeInTheDocument();
    });

    it("shows collapse button when expanded", () => {
      const node = createNode({
        path: "node-1",
        children: [createNode({ id: "child-1", pref_label: "Child" })],
      });

      render(
        <TreeNode
          {...defaultProps}
          node={node}
          expandedPaths={new Set(["node-1"])}
        />
      );

      expect(screen.getByRole("button", { name: /Collapse/i })).toBeInTheDocument();
    });

    it("calls onToggle with path when toggle clicked", () => {
      const onToggle = vi.fn();
      const node = createNode({
        path: "parent/child",
        children: [createNode({ id: "grandchild", pref_label: "Grandchild" })],
      });

      renderWithDnd(<TreeNode {...defaultProps} node={node} onToggle={onToggle} />);

      fireEvent.click(screen.getByRole("button", { name: /Expand/i }));

      expect(onToggle).toHaveBeenCalledWith("parent/child");
    });
  });

  describe("selection", () => {
    it("calls onSelect with node id when label clicked", () => {
      const onSelect = vi.fn();
      const node = createNode({ id: "my-node-id", pref_label: "My Node" });

      renderWithDnd(<TreeNode {...defaultProps} node={node} onSelect={onSelect} />);

      fireEvent.click(screen.getByText("My Node"));

      expect(onSelect).toHaveBeenCalledWith("my-node-id");
    });

    it("applies selected class when node is selected", () => {
      const node = createNode({ id: "selected-node" });

      render(
        <TreeNode {...defaultProps} node={node} selectedId="selected-node" />
      );

      const row = screen.getByText("Test Node").closest(".tree-node__row");
      expect(row).toHaveClass("tree-node__row--selected");
    });

    it("does not apply selected class when node is not selected", () => {
      const node = createNode({ id: "unselected-node" });

      render(
        <TreeNode {...defaultProps} node={node} selectedId="other-node" />
      );

      const row = screen.getByText("Test Node").closest(".tree-node__row");
      expect(row).not.toHaveClass("tree-node__row--selected");
    });
  });

  describe("multi-parent indicator", () => {
    it("shows multi-parent indicator when hasMultipleParents is true", () => {
      const node = createNode({
        hasMultipleParents: true,
        otherParentLabels: ["Parent A", "Parent B"],
      });

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      const indicator = screen.getByText("⑂");
      expect(indicator).toBeInTheDocument();
      expect(indicator).toHaveAttribute("title", "Also under: Parent A, Parent B");
    });

    it("does not show multi-parent indicator when hasMultipleParents is false", () => {
      const node = createNode({ hasMultipleParents: false });

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      expect(screen.queryByText("⑂")).not.toBeInTheDocument();
    });
  });

  describe("children rendering", () => {
    it("renders children when expanded", () => {
      const node = createNode({
        path: "parent",
        children: [
          createNode({ id: "child-1", pref_label: "Child One", path: "parent/child-1" }),
          createNode({ id: "child-2", pref_label: "Child Two", path: "parent/child-2" }),
        ],
      });

      render(
        <TreeNode
          {...defaultProps}
          node={node}
          expandedPaths={new Set(["parent"])}
        />
      );

      expect(screen.getByText("Child One")).toBeInTheDocument();
      expect(screen.getByText("Child Two")).toBeInTheDocument();
    });

    it("does not render children when collapsed", () => {
      const node = createNode({
        children: [
          createNode({ id: "child-1", pref_label: "Child One" }),
        ],
      });

      renderWithDnd(<TreeNode {...defaultProps} node={node} expandedPaths={new Set()} />);

      expect(screen.queryByText("Child One")).not.toBeInTheDocument();
    });
  });

  describe("drag handle", () => {
    it("renders drag handle with correct title", () => {
      const node = createNode();

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      const handle = screen.getByTitle("Drag to move");
      expect(handle).toBeInTheDocument();
      expect(handle).toHaveTextContent("⋮⋮");
    });
  });

  describe("add child button", () => {
    it("renders add child button when onAddChild provided", () => {
      const node = createNode();
      const onAddChild = vi.fn();

      renderWithDnd(<TreeNode {...defaultProps} node={node} onAddChild={onAddChild} />);

      expect(screen.getByRole("button", { name: /add child/i })).toBeInTheDocument();
    });

    it("does not render add child button when onAddChild not provided", () => {
      const node = createNode();

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      expect(screen.queryByRole("button", { name: /add child/i })).not.toBeInTheDocument();
    });

    it("calls onAddChild with concept id when clicked", () => {
      const node = createNode({ id: "parent-concept" });
      const onAddChild = vi.fn();

      renderWithDnd(<TreeNode {...defaultProps} node={node} onAddChild={onAddChild} />);

      fireEvent.click(screen.getByRole("button", { name: /add child/i }));

      expect(onAddChild).toHaveBeenCalledWith("parent-concept");
    });
  });

  describe("search match styling", () => {
    it("applies match class when matchStatus is 'match'", () => {
      const node = createNode({ matchStatus: "match" });
      searchQuery.value = "test";

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      const row = screen.getByText("Test Node").closest(".tree-node__row");
      expect(row).toHaveClass("tree-node__row--match");
    });

    it("applies dimmed class when matchStatus is 'none' and search is active", () => {
      const node = createNode({ matchStatus: "none" });
      searchQuery.value = "test";

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      const row = screen.getByText("Test Node").closest(".tree-node__row");
      expect(row).toHaveClass("tree-node__row--dimmed");
    });

    it("does not apply dimmed class when search is empty", () => {
      const node = createNode({ matchStatus: "none" });
      searchQuery.value = "";

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      const row = screen.getByText("Test Node").closest(".tree-node__row");
      expect(row).not.toHaveClass("tree-node__row--dimmed");
    });

    it("does not apply special class for ancestor matchStatus", () => {
      const node = createNode({ matchStatus: "ancestor" });
      searchQuery.value = "test";

      renderWithDnd(<TreeNode {...defaultProps} node={node} />);

      const row = screen.getByText("Test Node").closest(".tree-node__row");
      expect(row).not.toHaveClass("tree-node__row--match");
      expect(row).not.toHaveClass("tree-node__row--dimmed");
    });
  });
});
