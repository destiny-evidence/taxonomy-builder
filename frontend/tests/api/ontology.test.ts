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

  describe("get", () => {
    it("fetches the core ontology", async () => {
      const mockOntology = {
        classes: [
          { uri: "http://example.org/Person", label: "Person", comment: "A human being" },
        ],
        object_properties: [],
        datatype_properties: [],
      };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockOntology),
      });

      const result = await ontologyApi.get();

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/ontology",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockOntology);
    });

    it("returns classes with label and comment", async () => {
      const mockOntology = {
        classes: [
          { uri: "http://example.org/Person", label: "Person", comment: "A human being" },
          { uri: "http://example.org/Organization", label: "Organization", comment: null },
        ],
        object_properties: [],
        datatype_properties: [],
      };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockOntology),
      });

      const result = await ontologyApi.get();

      expect(result.classes).toHaveLength(2);
      expect(result.classes[0].label).toBe("Person");
      expect(result.classes[1].comment).toBeNull();
    });
  });
});
