import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { ontologyApi } from "../../src/api/ontology";

describe("ontologyApi", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  describe("listForProject", () => {
    it("fetches classes for a project", async () => {
      const mockClasses = [
        { id: "1", uri: "http://example.org/Person", label: "Person", description: "A human being" },
      ];
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockClasses),
      });

      const result = await ontologyApi.listForProject("project-123");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/classes",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockClasses);
    });

    it("returns classes with label and description", async () => {
      const mockClasses = [
        { id: "1", uri: "http://example.org/Person", label: "Person", description: "A human being" },
        { id: "2", uri: "http://example.org/Organization", label: "Organization", description: null },
      ];
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockClasses),
      });

      const result = await ontologyApi.listForProject("project-123");

      expect(result).toHaveLength(2);
      expect(result[0].label).toBe("Person");
      expect(result[1].description).toBeNull();
    });
  });
});
