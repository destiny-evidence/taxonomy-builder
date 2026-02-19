import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/preact";
import { SchemePreview } from "../../../src/components/properties/SchemePreview";
import { conceptsApi } from "../../../src/api/concepts";
import type { TreeNode } from "../../../src/types/models";

vi.mock("../../../src/api/concepts");

const mockTreeData: TreeNode[] = [
  {
    id: "concept-1",
    scheme_id: "scheme-1",
    identifier: "c1",
    pref_label: "Root Concept",
    definition: "A root concept",
    scope_note: null,
    uri: null,
    alt_labels: [],
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    narrower: [
      {
        id: "concept-2",
        scheme_id: "scheme-1",
        identifier: "c2",
        pref_label: "Child Concept",
        definition: null,
        scope_note: null,
        uri: null,
        alt_labels: [],
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        narrower: [],
      },
    ],
  },
];

describe("SchemePreview", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(conceptsApi.getTree).mockResolvedValue(mockTreeData);
  });

  it("loads tree data on mount", async () => {
    render(<SchemePreview schemeId="scheme-1" />);

    await waitFor(() => {
      expect(conceptsApi.getTree).toHaveBeenCalledWith("scheme-1");
    });
  });

  it("displays tree nodes after loading", async () => {
    render(<SchemePreview schemeId="scheme-1" />);

    await waitFor(() => {
      expect(screen.getByText("Root Concept")).toBeInTheDocument();
    });
  });

  it("shows loading state while fetching", () => {
    vi.mocked(conceptsApi.getTree).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<SchemePreview schemeId="scheme-1" />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows empty state when scheme has no concepts", async () => {
    vi.mocked(conceptsApi.getTree).mockResolvedValue([]);

    render(<SchemePreview schemeId="scheme-1" />);

    await waitFor(() => {
      expect(screen.getByText(/no concepts/i)).toBeInTheDocument();
    });
  });
});
