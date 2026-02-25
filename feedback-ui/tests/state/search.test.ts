import { describe, it, expect } from "vitest";

describe("search state", () => {
  it("returns empty results for empty query", async () => {
    const mod = await import("../../src/state/search");
    mod.searchQuery.value = "";
    expect(mod.searchResults.value).toEqual([]);
  });

  it("searches entity labels", async () => {
    const vocabMod = await import("../../src/state/vocabulary");
    const searchMod = await import("../../src/state/search");

    vocabMod.vocabulary.value = {
      format_version: "1",
      version: "1.0",
      title: "Test",
      published_at: "2024-01-01",
      publisher: null,
      pre_release: false,
      previous_version_id: null,
      project: { id: "p1", name: "Test", description: null, namespace: null },
      schemes: [
        {
          id: "s1",
          title: "Colors",
          description: null,
          uri: "http://example.org/s1",
          top_concepts: [],
          concepts: {
            c1: {
              pref_label: "Red",
              identifier: "red",
              uri: "http://example.org/red",
              definition: null,
              scope_note: null,
              alt_labels: ["Crimson"],
              broader: [],
              related: [],
            },
          },
        },
      ],
      classes: [
        {
          id: "cls1",
          identifier: "Paint",
          uri: "http://example.org/Paint",
          label: "Paint",
          description: null,
          scope_note: null,
        },
      ],
      properties: [],
    };

    searchMod.searchQuery.value = "red";
    const results = searchMod.searchResults.value;
    expect(results).toHaveLength(1);
    expect(results[0].type).toBe("concept");
    expect(results[0].label).toBe("Red");

    // Search by alt label
    searchMod.searchQuery.value = "crimson";
    expect(searchMod.searchResults.value).toHaveLength(1);
    expect(searchMod.searchResults.value[0].label).toBe("Red");

    // Search classes
    searchMod.searchQuery.value = "paint";
    expect(searchMod.searchResults.value).toHaveLength(1);
    expect(searchMod.searchResults.value[0].type).toBe("class");
  });
});
