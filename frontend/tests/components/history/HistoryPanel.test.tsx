import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/preact";
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
      project_id: null,
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
      project_id: null,
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
        // Action labels
        expect(screen.getByText("Updated")).toBeInTheDocument();
        expect(screen.getByText("Created")).toBeInTheDocument();
        // Entity type labels
        expect(screen.getAllByText("Concept")).toHaveLength(2);
        // Change descriptions (concept pref_labels)
        expect(screen.getByText("New Label")).toBeInTheDocument();
        expect(screen.getByText("Test Concept")).toBeInTheDocument();
        // Null user fallback
        expect(screen.getAllByText("Unknown")).toHaveLength(2);
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

    it("shows broader relationship labels", async () => {
      const broaderHistory: ChangeEvent[] = [
        {
          id: "event-1",
          timestamp: "2024-01-15T10:30:00Z",
          entity_type: "concept_broader",
          entity_id: "concept-123",
          scheme_id: "scheme-456",
          project_id: null,
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
          project_id: null,
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
          project_id: null,
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
          project_id: "project-1",
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
          project_id: "project-1",
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

  describe("entity type filtering", () => {
    const mixedHistory: ChangeEvent[] = [
      {
        id: "evt-concept",
        timestamp: "2024-01-15T10:30:00Z",
        entity_type: "concept",
        entity_id: "c-1",
        project_id: "p-1",
        scheme_id: "s-1",
        action: "create",
        before_state: null,
        after_state: { pref_label: "Dog" },
        user_id: null,
        user_display_name: null,
      },
      {
        id: "evt-property",
        timestamp: "2024-01-15T09:00:00Z",
        entity_type: "property",
        entity_id: "prop-1",
        project_id: "p-1",
        scheme_id: null,
        action: "create",
        before_state: null,
        after_state: { label: "Severity" },
        user_id: null,
        user_display_name: null,
      },
      {
        id: "evt-broader",
        timestamp: "2024-01-15T08:00:00Z",
        entity_type: "concept_broader",
        entity_id: "c-1",
        project_id: "p-1",
        scheme_id: "s-1",
        action: "create",
        before_state: null,
        after_state: { concept_label: "Dog", broader_label: "Animal" },
        user_id: null,
        user_display_name: null,
      },
    ];

    it("filters by entity type and resets", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mixedHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "s-1" }} />);

      await waitFor(() => {
        expect(screen.getAllByText("Dog")).toHaveLength(2);
      });

      // Open filter disclosure and select Properties — concept and broader events hidden
      fireEvent.click(screen.getByText(/filter:/i));
      fireEvent.click(screen.getByLabelText("Properties"));
      expect(screen.getByText("Severity")).toBeInTheDocument();
      expect(screen.queryByText("Dog")).not.toBeInTheDocument();
      expect(screen.queryByText("Animal")).not.toBeInTheDocument();

      // Reset — all events visible again
      fireEvent.click(screen.getByText("Show all changes"));
      expect(screen.getAllByText("Dog")).toHaveLength(2);
      expect(screen.getByText("Severity")).toBeInTheDocument();
      expect(screen.getByText("Animal")).toBeInTheDocument();
    });

    it("selecting multiple filters shows union", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mixedHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "s-1" }} />);

      await waitFor(() => {
        expect(screen.getAllByText("Dog")).toHaveLength(2);
      });

      fireEvent.click(screen.getByText(/filter:/i));
      fireEvent.click(screen.getByLabelText("Concepts"));
      fireEvent.click(screen.getByLabelText("Relationships"));

      // Concept and broader visible, property hidden
      expect(screen.getAllByText("Dog")).toHaveLength(2);
      expect(screen.getByText("Animal")).toBeInTheDocument();
      expect(screen.queryByText("Severity")).not.toBeInTheDocument();
    });

    it("shows 'no changes match' when filter excludes all events", async () => {
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mixedHistory);

      const { rerender } = render(
        <HistoryPanel source={{ type: "scheme", id: "s-1" }} refreshKey={0} />
      );

      await waitFor(() => {
        expect(screen.getAllByText("Dog")).toHaveLength(2);
      });

      // Select "Properties" filter
      fireEvent.click(screen.getByText(/filter:/i));
      fireEvent.click(screen.getByLabelText("Properties"));
      expect(screen.getByText("Severity")).toBeInTheDocument();

      // Data refreshes with only concept events (no properties)
      const conceptOnly: ChangeEvent[] = [mixedHistory[0]];
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(conceptOnly);
      rerender(
        <HistoryPanel source={{ type: "scheme", id: "s-1" }} refreshKey={1} />
      );

      await waitFor(() => {
        expect(screen.getByText(/no changes match/i)).toBeInTheDocument();
      });
    });

    it("only shows filter groups that have matching events", async () => {
      // History with concept + broader only — no property/scheme/project/version events
      const limitedHistory: ChangeEvent[] = [mixedHistory[0], mixedHistory[2]];
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(limitedHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "s-1" }} />);

      await waitFor(() => {
        expect(screen.getAllByText("Dog")).toHaveLength(2);
      });

      fireEvent.click(screen.getByText(/filter:/i));

      expect(screen.getByLabelText("Concepts")).toBeInTheDocument();
      expect(screen.getByLabelText("Relationships")).toBeInTheDocument();
      expect(screen.queryByLabelText("Properties")).not.toBeInTheDocument();
      expect(screen.queryByLabelText("Schemes")).not.toBeInTheDocument();
      expect(screen.queryByLabelText("Project settings")).not.toBeInTheDocument();
      expect(screen.queryByLabelText("Published versions")).not.toBeInTheDocument();
    });

    it("does not show filter when only one entity type category exists", async () => {
      // Only concept events — filter would have just one option
      vi.mocked(historyApi.getSchemeHistory).mockResolvedValue(mockHistory);

      render(<HistoryPanel source={{ type: "scheme", id: "s-1" }} />);

      await waitFor(() => {
        expect(screen.getByText("New Label")).toBeInTheDocument();
      });

      expect(screen.queryByText(/filter:/i)).not.toBeInTheDocument();
    });
  });
});
