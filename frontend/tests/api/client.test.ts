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
        json: () => Promise.resolve({ data: "test" }),
      });

      await api.get("/projects");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects",
        expect.objectContaining({ method: "GET" })
      );
    });

    it("parses JSON response", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: "123", name: "Test" }),
      });

      const result = await api.get<{ id: string; name: string }>("/projects/123");

      expect(result).toEqual({ id: "123", name: "Test" });
    });
  });

  describe("api.post", () => {
    it("sends JSON body", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: () => Promise.resolve({ id: "new" }),
      });

      await api.post("/projects", { name: "New Project" });

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ name: "New Project" }),
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

      const result = await api.delete("/projects/123");

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

      await expect(api.get("/projects/missing")).rejects.toThrow(ApiError);
    });

    it("includes status code in ApiError", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: "Not found" }),
      });

      try {
        await api.get("/projects/missing");
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).status).toBe(404);
      }
    });

    it("uses error detail message when available", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 409,
        json: () => Promise.resolve({ detail: "Project already exists" }),
      });

      await expect(api.post("/projects", {})).rejects.toThrow("Project already exists");
    });

    it("falls back to status code message when no detail", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error("Invalid JSON")),
      });

      await expect(api.get("/projects")).rejects.toThrow("Request failed: 500");
    });
  });
});
