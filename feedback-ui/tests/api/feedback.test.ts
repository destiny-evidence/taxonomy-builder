import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { postFeedback } from "../../src/api/feedback";

describe("feedback api", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  describe("postFeedback", () => {
    it("calls POST /feedback/{projectId} with body", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ status: "ok" }),
      });

      const result = await postFeedback("proj-123", "Looks good!");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/proj-123",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ body: "Looks good!" }),
        })
      );
      expect(result).toEqual({ status: "ok" });
    });
  });
});
