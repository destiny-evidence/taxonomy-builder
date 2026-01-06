import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/preact";
import { HistoryPanel } from "../../../src/components/history/HistoryPanel";
import * as historyApi from "../../../src/api/history";
import type { ChangeEvent } from "../../../src/types/models";

vi.mock("../../../src/api/history");

describe("HistoryPanel", () => {
  const mockHistory: ChangeEvent[] = [
    {
      id: "event-1",
      timestamp: "2024-01-15T10:30:00Z",
      entity_type: "concept",
      entity_id: "concept-123",
      scheme_id: "scheme-456",
      action: "update",
      before_state: { pref_label: "Old Label" },
      after_state: { pref_label: "New Label" },
      user_id: null,
    },
    {
      id: "event-2",
      timestamp: "2024-01-15T09:00:00Z",
      entity_type: "concept",
      entity_id: "concept-123",
      scheme_id: "scheme-456",
      action: "create",
      before_state: null,
      after_state: { pref_label: "New Label" },
      user_id: null,
    },
  ];

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders loading state initially", () => {
    vi.mocked(historyApi.getSchemeHistory).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<HistoryPanel schemeId="scheme-456" />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders list of changes after loading", async () => {
    vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mockHistory);

    render(<HistoryPanel schemeId="scheme-456" />);

    await waitFor(() => {
      expect(screen.getByText(/update/i)).toBeInTheDocument();
      expect(screen.getByText(/create/i)).toBeInTheDocument();
    });
  });

  it("renders empty state when no history", async () => {
    vi.mocked(historyApi.getSchemeHistory).mockResolvedValue([]);

    render(<HistoryPanel schemeId="scheme-456" />);

    await waitFor(() => {
      expect(screen.getByText(/no history/i)).toBeInTheDocument();
    });
  });

  it("renders error state on failure", async () => {
    vi.mocked(historyApi.getSchemeHistory).mockRejectedValue(
      new Error("Failed to fetch")
    );

    render(<HistoryPanel schemeId="scheme-456" />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
