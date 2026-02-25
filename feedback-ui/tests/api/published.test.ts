import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  getRootIndex,
  getProjectIndex,
  getVocabulary,
  type RootIndex,
  type ProjectIndex,
  type Vocabulary,
} from "../../src/api/published";

const PROJ_ID = "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb";

const ROOT_INDEX: RootIndex = {
  format_version: "1.0",
  projects: [
    {
      id: PROJ_ID,
      name: "Test Project",
      description: "A test project",
      latest_version: "1.0",
    },
  ],
};

const PROJECT_INDEX: ProjectIndex = {
  format_version: "1.0",
  project: {
    id: PROJ_ID,
    name: "Test Project",
    description: "A test project",
    namespace: "https://example.org/test/",
  },
  latest_version: "1.0",
  versions: [
    {
      version: "1.0",
      title: "First release",
      published_at: "2025-06-01T12:00:00+00:00",
      publisher: "Alice",
      pre_release: false,
      previous_version_id: null,
      notes: null,
      content_summary: { schemes: 1, concepts: 2, properties: 1, classes: 1 },
    },
  ],
};

const VOCABULARY: Vocabulary = {
  format_version: "1.0",
  version: "1.0",
  title: "First release",
  published_at: "2025-06-01T12:00:00+00:00",
  publisher: "Alice",
  pre_release: false,
  previous_version_id: null,
  project: {
    id: PROJ_ID,
    name: "Test Project",
    description: "A test project",
    namespace: "https://example.org/test/",
  },
  schemes: [
    {
      id: "cccccccc-1111-2222-3333-dddddddddddd",
      title: "Test Scheme",
      description: null,
      uri: "https://example.org/test/scheme",
      top_concepts: ["eeeeeeee-1111-2222-3333-ffffffffffff"],
      concepts: {
        "eeeeeeee-1111-2222-3333-ffffffffffff": {
          pref_label: "Root Concept",
          identifier: "root-concept",
          uri: "https://example.org/test/scheme/root-concept",
          definition: "The root",
          scope_note: null,
          alt_labels: ["RC"],
          broader: [],
          related: [],
        },
      },
    },
  ],
  classes: [
    {
      id: "11111111-aaaa-bbbb-cccc-222222222222",
      identifier: "Finding",
      uri: "https://example.org/test/Finding",
      label: "Finding",
      description: null,
      scope_note: null,
    },
  ],
  properties: [
    {
      id: "33333333-aaaa-bbbb-cccc-444444444444",
      identifier: "severity",
      uri: "https://example.org/test/severity",
      label: "Severity",
      description: null,
      domain_class_uri: "https://example.org/test/Finding",
      range_scheme_id: "cccccccc-1111-2222-3333-dddddddddddd",
      range_scheme_uri: "https://example.org/test/scheme",
      range_datatype: null,
      cardinality: "single",
      required: true,
    },
  ],
};

describe("published content client", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  function mockOk(body: unknown) {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(body),
    });
  }

  function mockError(status: number) {
    mockFetch.mockResolvedValue({
      ok: false,
      status,
      statusText: "Not Found",
    });
  }

  describe("getRootIndex", () => {
    it("fetches /published/index.json", async () => {
      mockOk(ROOT_INDEX);

      const result = await getRootIndex();

      expect(mockFetch).toHaveBeenCalledWith("/published/index.json");
      expect(result).toEqual(ROOT_INDEX);
    });

    it("throws on non-ok response", async () => {
      mockError(500);

      await expect(getRootIndex()).rejects.toThrow(
        "Failed to fetch /published/index.json: 500"
      );
    });
  });

  describe("getProjectIndex", () => {
    it("fetches /published/{projectId}/index.json", async () => {
      mockOk(PROJECT_INDEX);

      const result = await getProjectIndex(PROJ_ID);

      expect(mockFetch).toHaveBeenCalledWith(
        `/published/${PROJ_ID}/index.json`
      );
      expect(result).toEqual(PROJECT_INDEX);
    });

    it("throws on non-ok response", async () => {
      mockError(404);

      await expect(getProjectIndex(PROJ_ID)).rejects.toThrow("404");
    });
  });

  describe("getVocabulary", () => {
    it("fetches /published/{projectId}/{version}/vocabulary.json", async () => {
      mockOk(VOCABULARY);

      const result = await getVocabulary(PROJ_ID, "1.0");

      expect(mockFetch).toHaveBeenCalledWith(
        `/published/${PROJ_ID}/1.0/vocabulary.json`
      );
      expect(result).toEqual(VOCABULARY);
    });

    it("throws on non-ok response", async () => {
      mockError(404);

      await expect(getVocabulary(PROJ_ID, "2.0")).rejects.toThrow("404");
    });
  });
});
