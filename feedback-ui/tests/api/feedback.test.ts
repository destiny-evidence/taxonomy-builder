import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getFeedback, postFeedback, deleteFeedback } from "../../src/api/feedback";

describe("feedback api", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  describe("getFeedback", () => {
    it("calls GET /feedback/ui/{projectId}", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      });

      const result = await getFeedback("proj-123");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/ui/proj-123",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual([]);
    });
  });

  describe("postFeedback", () => {
    it("calls POST /feedback/ui/{projectId} with body", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ status: "ok" }),
      });

      const result = await postFeedback("proj-123", "Looks good!");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/ui/proj-123",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ body: "Looks good!" }),
        })
      );
      expect(result).toEqual({ status: "ok" });
    });
  });

  describe("deleteFeedback", () => {
    it("calls DELETE /feedback/ui/{projectId}", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
      });

      await deleteFeedback("proj-123");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/ui/proj-123",
        expect.objectContaining({ method: "DELETE" })
      );
    });
  });
});
