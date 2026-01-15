import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/preact";
import { route } from "preact-router";
import { SchemeDetailPage } from "../../src/pages/SchemeDetailPage";
import { schemesApi } from "../../src/api/schemes";

vi.mock("preact-router", () => ({
  route: vi.fn(),
}));

vi.mock("../../src/api/schemes", () => ({
  schemesApi: {
    get: vi.fn(),
  },
}));

describe("SchemeDetailPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("redirects to workspace URL after loading scheme", async () => {
    const mockScheme = {
      id: "scheme-123",
      project_id: "project-456",
      title: "Test Scheme",
      description: null,
      uri: "http://example.org/scheme",
      publisher: null,
      version: null,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    };

    vi.mocked(schemesApi.get).mockResolvedValue(mockScheme);

    render(<SchemeDetailPage schemeId="scheme-123" />);

    // Shows loading state initially
    expect(screen.getByText(/redirecting/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(route).toHaveBeenCalledWith(
        "/projects/project-456/schemes/scheme-123",
        true
      );
    });
  });

  it("shows error when scheme not found", async () => {
    vi.mocked(schemesApi.get).mockRejectedValue(new Error("Not found"));

    render(<SchemeDetailPage schemeId="scheme-123" />);

    await waitFor(() => {
      expect(screen.getByText(/not found/i)).toBeInTheDocument();
    });
  });
});
