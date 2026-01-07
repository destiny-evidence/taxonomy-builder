import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/preact";
import { VersionsPanel } from "../../../src/components/versions/VersionsPanel";
import * as versionsApi from "../../../src/api/versions";
import type { PublishedVersion } from "../../../src/types/models";

vi.mock("../../../src/api/versions");

// Mock HTMLDialogElement methods for jsdom
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn();
  HTMLDialogElement.prototype.close = vi.fn();
});

describe("VersionsPanel", () => {
  const mockVersions: PublishedVersion[] = [
    {
      id: "version-1",
      scheme_id: "scheme-456",
      version_label: "2.0",
      published_at: "2024-01-15T10:30:00Z",
      snapshot: { scheme: {}, concepts: [] },
      notes: "Second release",
    },
    {
      id: "version-2",
      scheme_id: "scheme-456",
      version_label: "1.0",
      published_at: "2024-01-01T09:00:00Z",
      snapshot: { scheme: {}, concepts: [] },
      notes: "Initial release",
    },
  ];

  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading state initially", () => {
    vi.mocked(versionsApi.listVersions).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<VersionsPanel schemeId="scheme-456" />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders list of versions after loading", async () => {
    vi.mocked(versionsApi.listVersions).mockResolvedValue(mockVersions);

    render(<VersionsPanel schemeId="scheme-456" />);

    await waitFor(() => {
      expect(screen.getByText("v2.0")).toBeInTheDocument();
      expect(screen.getByText("v1.0")).toBeInTheDocument();
    });
  });

  it("renders empty state when no versions", async () => {
    vi.mocked(versionsApi.listVersions).mockResolvedValue([]);

    render(<VersionsPanel schemeId="scheme-456" />);

    await waitFor(() => {
      expect(screen.getByText(/no versions/i)).toBeInTheDocument();
    });
  });

  it("renders error state on failure", async () => {
    vi.mocked(versionsApi.listVersions).mockRejectedValue(
      new Error("Failed to fetch")
    );

    render(<VersionsPanel schemeId="scheme-456" />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it("renders export button for each version", async () => {
    vi.mocked(versionsApi.listVersions).mockResolvedValue(mockVersions);

    render(<VersionsPanel schemeId="scheme-456" />);

    await waitFor(() => {
      const exportButtons = screen.getAllByText("Export");
      expect(exportButtons).toHaveLength(2);
    });
  });

  it("calls window.open with export URL when export clicked", async () => {
    vi.mocked(versionsApi.listVersions).mockResolvedValue(mockVersions);
    const mockOpen = vi.fn();
    vi.stubGlobal("open", mockOpen);

    render(<VersionsPanel schemeId="scheme-456" />);

    await waitFor(() => {
      expect(screen.getByText("v2.0")).toBeInTheDocument();
    });

    const exportButtons = screen.getAllByText("Export");
    fireEvent.click(exportButtons[0]);

    expect(mockOpen).toHaveBeenCalledWith(
      "/api/versions/version-1/export",
      "_blank"
    );
  });

  it("renders publish button", async () => {
    vi.mocked(versionsApi.listVersions).mockResolvedValue([]);

    render(<VersionsPanel schemeId="scheme-456" />);

    await waitFor(() => {
      expect(screen.getByText("Publish New Version")).toBeInTheDocument();
    });
  });
});
