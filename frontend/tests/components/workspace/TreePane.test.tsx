import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { TreePane } from "../../../src/components/workspace/TreePane";
import { currentScheme } from "../../../src/state/schemes";
import { treeLoading } from "../../../src/state/concepts";
import type { ConceptScheme } from "../../../src/types/models";

// Mock TreeView since it has complex dependencies
vi.mock("../../../src/components/tree/TreeView", () => ({
  TreeView: ({ schemeId, onCreate }: { schemeId: string; onCreate?: () => void }) => (
    <div data-testid="tree-view" data-has-oncreate={onCreate ? "true" : "false"}>
      TreeView for {schemeId}
    </div>
  ),
}));

// Mock TreeControls
vi.mock("../../../src/components/tree/TreeControls", () => ({
  TreeControls: () => <div data-testid="tree-controls">TreeControls</div>,
}));

// Mock HistoryPanel
vi.mock("../../../src/components/history/HistoryPanel", () => ({
  HistoryPanel: ({ schemeId }: { schemeId: string }) => (
    <div data-testid="history-panel">History for {schemeId}</div>
  ),
}));

// Mock VersionsPanel
vi.mock("../../../src/components/versions/VersionsPanel", () => ({
  VersionsPanel: ({ schemeId }: { schemeId: string }) => (
    <div data-testid="versions-panel">Versions for {schemeId}</div>
  ),
}));

const mockScheme: ConceptScheme = {
  id: "scheme-1",
  project_id: "proj-1",
  title: "Animal Taxonomy",
  description: "A taxonomy of animals",
  uri: "http://example.org/animals",
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

  it("passes onCreate to TreeView when provided", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
        onCreate={() => {}}
      />
    );

    expect(screen.getByTestId("tree-view")).toHaveAttribute("data-has-oncreate", "true");
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

  it("renders collapsible History section in footer", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
      />
    );

    expect(screen.getByRole("button", { name: /history/i })).toBeInTheDocument();
  });

  it("expands History section when clicked", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
      />
    );

    const historyButton = screen.getByRole("button", { name: /history/i });
    fireEvent.click(historyButton);

    expect(screen.getByTestId("history-panel")).toBeInTheDocument();
    expect(historyButton).toHaveAttribute("aria-expanded", "true");
  });

  it("collapses section when clicked again", () => {
    render(
      <TreePane
        schemeId="scheme-1"
        onExpandAll={() => {}}
        onCollapseAll={() => {}}
        onRefresh={async () => {}}
      />
    );

    const historyButton = screen.getByRole("button", { name: /history/i });

    // Open
    fireEvent.click(historyButton);
    expect(screen.getByTestId("history-panel")).toBeInTheDocument();

    // Close
    fireEvent.click(historyButton);
    expect(screen.queryByTestId("history-panel")).not.toBeInTheDocument();
    expect(historyButton).toHaveAttribute("aria-expanded", "false");
  });
});
