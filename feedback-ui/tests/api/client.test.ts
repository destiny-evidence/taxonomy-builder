import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api, ApiError } from "../../src/api/client";

describe("api client", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  describe("api.get", () => {
    it("constructs correct URL with API_BASE", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      });

      await api.get("/feedback/ui/some-id");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/ui/some-id",
        expect.objectContaining({ method: "GET" })
      );
    });

    it("parses JSON response", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([{ id: "1", body: "test" }]),
      });

      const result = await api.get("/feedback/ui/proj-1");

      expect(result).toEqual([{ id: "1", body: "test" }]);
    });
  });

  describe("api.post", () => {
    it("sends JSON body", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ status: "ok" }),
      });

      await api.post("/feedback/ui/proj-1", { body: "Great!" });

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/feedback/ui/proj-1",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ body: "Great!" }),
        })
      );
    });
  });

  describe("api.delete", () => {
    it("handles 204 no content response", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
      });

      const result = await api.delete("/feedback/ui/proj-1");

      expect(result).toBeUndefined();
    });
  });

  describe("error handling", () => {
    it("throws ApiError on non-ok response", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: "Not found" }),
      });

      await expect(api.get("/feedback/ui/missing")).rejects.toThrow(ApiError);
    });

    it("clears auth on 401", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: "Unauthorized" }),
      });

      await expect(api.get("/feedback/ui/proj-1")).rejects.toThrow(ApiError);
    });

    it("falls back to status code message when no detail", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error("Invalid JSON")),
      });

      await expect(api.get("/feedback/ui/proj-1")).rejects.toThrow(
        "Request failed: 500"
      );
    });
  });
});
