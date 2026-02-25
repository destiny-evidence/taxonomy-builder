import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { feedbackApi } from "../../src/api/feedback";

describe("feedback api", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  describe("create", () => {
    it("calls POST /feedback/{projectId} with full body", async () => {
      const mockResponse = { id: "fb-1", status: "open" };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await feedbackApi.create("proj-123", {
        snapshot_version: "1.0",
        entity_type: "concept",
        entity_id: "c-1",
        entity_label: "Test",
        feedback_type: "unclear_definition",
        content: "Needs clarification",
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/proj-123",
        expect.objectContaining({ method: "POST" })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("listMine", () => {
    it("calls GET /feedback/{projectId}/mine", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      });

      await feedbackApi.listMine("proj-123");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/proj-123/mine",
        expect.objectContaining({ method: "GET" })
      );
    });

    it("appends query params when provided", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      });

      await feedbackApi.listMine("proj-123", {
        version: "1.0",
        entity_type: "concept",
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/proj-123/mine?version=1.0&entity_type=concept",
        expect.objectContaining({ method: "GET" })
      );
    });
  });

  describe("deleteOwn", () => {
    it("calls DELETE /feedback/{feedbackId}", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
      });

      await feedbackApi.deleteOwn("fb-1");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/fb-1",
        expect.objectContaining({ method: "DELETE" })
      );
    });
  });
});
