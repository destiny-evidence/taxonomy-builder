import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/preact";
import { TreePane } from "../../../src/components/workspace/TreePane";
import { currentScheme } from "../../../src/state/schemes";
import { treeLoading } from "../../../src/state/concepts";
import type { ConceptScheme } from "../../../src/types/models";

// Mock TreeView since it has complex dependencies
vi.mock("../../../src/components/tree/TreeView", () => ({
  TreeView: ({ schemeId }: { schemeId: string }) => (
    <div data-testid="tree-view">TreeView for {schemeId}</div>
  ),
}));

// Mock TreeControls
vi.mock("../../../src/components/tree/TreeControls", () => ({
  TreeControls: () => <div data-testid="tree-controls">TreeControls</div>,
}));

const mockScheme: ConceptScheme = {
  id: "scheme-1",
  project_id: "proj-1",
  title: "Animal Taxonomy",
  description: "A taxonomy of animals",
  uri: "http://example.org/animals",
  publisher: null,
  version: null,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("TreePane", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    currentScheme.value = mockScheme;
    treeLoading.value = false;
  });

  it("renders scheme title in header", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
      />
    );

    expect(screen.getByText("Animal Taxonomy")).toBeInTheDocument();
  });

  it("renders TreeView component", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
      />
    );

    expect(screen.getByTestId("tree-view")).toBeInTheDocument();
  });

  it("renders TreeControls", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
      />
    );

    expect(screen.getByTestId("tree-controls")).toBeInTheDocument();
  });

  it("shows loading state when tree is loading", () => {
    treeLoading.value = true;

    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
      />
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows placeholder when no scheme is selected", () => {
    currentScheme.value = null;

    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
      />
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders Add Concept button when onCreate provided", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
        onCreate={() => {}}
      />
    );

    expect(screen.getByText("Add Concept")).toBeInTheDocument();
  });

  it("renders Export button when onExport provided", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
        onExport={() => {}}
      />
    );

    expect(screen.getByText("Export")).toBeInTheDocument();
  });

  it("renders History button when onHistory provided", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
        onHistory={() => {}}
      />
    );

    expect(screen.getByText("History")).toBeInTheDocument();
  });

  it("renders Versions button when onVersions provided", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
        onVersions={() => {}}
      />
    );

    expect(screen.getByText("Versions")).toBeInTheDocument();
  });
});
