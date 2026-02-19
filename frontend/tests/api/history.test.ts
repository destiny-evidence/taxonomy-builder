import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getProjectHistory, getPropertyHistory } from "../../src/api/history";

describe("history API", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  describe("getProjectHistory", () => {
    it("fetches history for a project", async () => {
      const mockEvents = [{ id: "evt-1", action: "create", entity_type: "property" }];
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockEvents),
      });

      const result = await getProjectHistory("project-123");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/history",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockEvents);
    });

    it("passes limit and offset as query params", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      });

      await getProjectHistory("project-123", 10, 20);

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/history?limit=10&offset=20",
        expect.objectContaining({ method: "GET" })
      );
    });
  });

  describe("getPropertyHistory", () => {
    it("fetches history for a property", async () => {
      const mockEvents = [{ id: "evt-1", action: "update", entity_type: "property" }];
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockEvents),
      });

      const result = await getPropertyHistory("prop-456");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/properties/prop-456/history",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockEvents);
    });
  });
});
