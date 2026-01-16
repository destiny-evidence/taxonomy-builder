import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { TreeView } from "../../../src/components/tree/TreeView";
import {
  treeLoading,
  treeData,
  expandedPaths,
  selectedConceptId,
} from "../../../src/state/concepts";

describe("TreeView", () => {
  beforeEach(() => {
    treeLoading.value = false;
    treeData.value = [];
    expandedPaths.value = new Set();
    selectedConceptId.value = null;
  });

  it("renders Add Concept button when onCreate provided", () => {
    const onCreate = vi.fn();

    render(<TreeView schemeId="scheme-1" onRefresh={() => {}} onCreate={onCreate} />);

    expect(screen.getByRole("button", { name: /add concept/i })).toBeInTheDocument();
  });

  it("calls onCreate when Add Concept button clicked", () => {
    const onCreate = vi.fn();

    render(<TreeView schemeId="scheme-1" onRefresh={() => {}} onCreate={onCreate} />);

    fireEvent.click(screen.getByRole("button", { name: /add concept/i }));

    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  it("shows Add Concept button in empty state", () => {
    const onCreate = vi.fn();

    render(<TreeView schemeId="scheme-1" onRefresh={() => {}} onCreate={onCreate} />);

    expect(screen.getByText(/no concepts yet/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add concept/i })).toBeInTheDocument();
  });

  it("shows Add Concept button below tree when concepts exist", () => {
    treeData.value = [
      {
        id: "concept-1",
        scheme_id: "scheme-1",
        identifier: "concept-1",
        pref_label: "Test Concept",
        definition: null,
        scope_note: null,
        uri: null,
        alt_labels: [],
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        narrower: [],
      },
    ];
    const onCreate = vi.fn();

    render(<TreeView schemeId="scheme-1" onRefresh={() => {}} onCreate={onCreate} />);

    expect(screen.getByText("Test Concept")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add concept/i })).toBeInTheDocument();
  });
});
