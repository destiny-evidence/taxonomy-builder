import { describe, it, expect } from "vitest";
import { makeVocabulary, makeConcept } from "../fixtures";

describe("search state", () => {
  it("returns empty results for empty query", async () => {
    const mod = await import("../../src/state/search");
    mod.searchQuery.value = "";
    expect(mod.searchResults.value).toEqual([]);
  });

  it("searches entity labels", async () => {
    const vocabMod = await import("../../src/state/vocabulary");
    const searchMod = await import("../../src/state/search");

    vocabMod.vocabulary.value = makeVocabulary({
      schemes: [
        {
          id: "s1",
          title: "Colors",
          description: null,
          uri: "http://example.org/s1",
          top_concepts: [],
          concepts: {
            c1: makeConcept({
              pref_label: "Red",
              identifier: "red",
              alt_labels: ["Crimson"],
            }),
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
    });

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
