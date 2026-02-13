import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
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
      user_display_name: null,
    },
    {
      id: "event-2",
      timestamp: "2024-01-15T09:00:00Z",
      entity_type: "concept",
      entity_id: "concept-123",
      scheme_id: "scheme-456",
      action: "create",
      before_state: null,
      after_state: { pref_label: "Test Concept" },
      user_id: null,
      user_display_name: null,
    },
  ];

  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("scheme source", () => {
    it("renders loading state initially", () => {
      vi.mocked(historyApi.getSchemeHistory).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it("renders list of changes after loading", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mockHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getByText("Updated")).toBeInTheDocument();
        expect(screen.getByText("Created")).toBeInTheDocument();
      });
    });

    it("renders empty state when no history", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue([]);

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getByText(/no history/i)).toBeInTheDocument();
      });
    });

    it("renders error state on failure", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockRejectedValue(
        new Error("Failed to fetch")
      );

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });

    it("renders human-readable entity type", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mockHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getAllByText("Concept")).toHaveLength(2);
      });
    });

    it("shows concept label in bold in change description", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mockHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getByText("New Label")).toBeInTheDocument();
        expect(screen.getByText("Test Concept")).toBeInTheDocument();
      });
    });

    it("shows broader relationship labels", async () => {
      const broaderHistory: ChangeEvent[] = [
        {
          id: "event-1",
          timestamp: "2024-01-15T10:30:00Z",
          entity_type: "concept_broader",
          entity_id: "concept-123",
          scheme_id: "scheme-456",
          action: "create",
          before_state: null,
          after_state: {
            concept_id: "concept-123",
            broader_concept_id: "concept-456",
            concept_label: "Dogs",
            broader_label: "Animals",
          },
          user_id: null,
          user_display_name: null,
        },
      ];
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(broaderHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getByText("Dogs")).toBeInTheDocument();
        expect(screen.getByText("Animals")).toBeInTheDocument();
      });
    });

    it("renders disclosure for viewing full changes", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mockHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getAllByText("View changes")).toHaveLength(2);
      });
    });

    it("displays user display name when available", async () => {
      const historyWithUser: ChangeEvent[] = [
        {
          id: "event-1",
          timestamp: "2024-01-15T10:30:00Z",
          entity_type: "concept",
          entity_id: "concept-123",
          scheme_id: "scheme-456",
          action: "update",
          before_state: { pref_label: "Old Label" },
          after_state: { pref_label: "New Label" },
          user_id: "user-123",
          user_display_name: "Jane Smith",
        },
      ];
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(historyWithUser);

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getByText("Jane Smith")).toBeInTheDocument();
      });
    });

    it("displays 'Unknown' when user_display_name is null", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mockHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getAllByText("Unknown")).toHaveLength(2);
      });
    });

    it("re-fetches when refreshKey changes", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mockHistory);

      const { rerender } = render(
        <HistoryPanel source={{ type: "scheme", id: "scheme-456" }} refreshKey={0} />
      );

      await waitFor(() => {
        expect(historyApi.getSchemeHistory).toHaveBeenCalledTimes(1);
      });

      rerender(
        <HistoryPanel source={{ type: "scheme", id: "scheme-456" }} refreshKey={1} />
      );

      await waitFor(() => {
        expect(historyApi.getSchemeHistory).toHaveBeenCalledTimes(2);
      });
    });

  });

  describe("project source", () => {
    it("calls getProjectHistory with the project id", async () => {
      vi.mocked(historyApi.getProjectHistory).mockResolvedValue([]);

      render(<HistoryPanel source={{ type: "project", id: "project-123" }} />);

      await waitFor(() => {
        expect(historyApi.getProjectHistory).toHaveBeenCalledWith("project-123");
      });
    });
  });

  describe("ChangeDescription for new entity types", () => {
    it("shows property label for property events", async () => {
      const propertyEvent: ChangeEvent[] = [
        {
          id: "event-20",
          timestamp: "2024-01-15T10:30:00Z",
          entity_type: "property",
          entity_id: "prop-1",
          scheme_id: null,
          action: "create",
          before_state: null,
          after_state: { label: "Finding Name" },
          user_id: null,
          user_display_name: null,
        },
      ];
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(propertyEvent);

      render(<HistoryPanel source={{ type: "scheme", id: "scheme-456" }} />);

      await waitFor(() => {
        expect(screen.getByText("Finding Name")).toBeInTheDocument();
      });
    });

    it("shows project name for project events", async () => {
      const projectEvent: ChangeEvent[] = [
        {
          id: "event-21",
          timestamp: "2024-01-15T10:30:00Z",
          entity_type: "project",
          entity_id: "project-1",
          scheme_id: null,
          action: "update",
          before_state: { name: "Old Project" },
          after_state: { name: "My Project" },
          user_id: null,
          user_display_name: null,
        },
      ];
      vi.mocked(historyApi.getProjectHistory).mockResolvedValue(projectEvent);

      render(<HistoryPanel source={{ type: "project", id: "project-1" }} />);

      await waitFor(() => {
        expect(screen.getByText("My Project")).toBeInTheDocument();
      });
    });

    it("shows scheme title for concept_scheme events", async () => {
      const schemeEvent: ChangeEvent[] = [
        {
          id: "event-22",
          timestamp: "2024-01-15T10:30:00Z",
          entity_type: "concept_scheme",
          entity_id: "scheme-1",
          scheme_id: null,
          action: "create",
          before_state: null,
          after_state: { title: "My Taxonomy" },
          user_id: null,
          user_display_name: null,
        },
      ];
      vi.mocked(historyApi.getProjectHistory).mockResolvedValue(schemeEvent);

      render(<HistoryPanel source={{ type: "project", id: "project-1" }} />);

      await waitFor(() => {
        expect(screen.getByText("My Taxonomy")).toBeInTheDocument();
      });
    });
  });
});
