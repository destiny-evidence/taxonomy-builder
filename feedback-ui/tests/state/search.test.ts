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
          superclasses: [],
          subclasses: [],
          restrictions: [],
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

  it("conceptMatchesSearch matches pref_label case-insensitively", async () => {
    const { conceptMatchesSearch } = await import("../../src/state/search");

    expect(conceptMatchesSearch("Red", [], "red")).toBe(true);
    expect(conceptMatchesSearch("Red", [], "RED")).toBe(true);
    expect(conceptMatchesSearch("Red", [], "blue")).toBe(false);
    expect(conceptMatchesSearch("Red", ["Crimson"], "crim")).toBe(true);
    expect(conceptMatchesSearch("Red", [], "")).toBe(true);
  });

  it("searchFilteredConceptTrees annotates match status", async () => {
    const vocabMod = await import("../../src/state/vocabulary");
    const searchMod = await import("../../src/state/search");

    vocabMod.vocabulary.value = makeVocabulary({
      schemes: [
        {
          id: "s1",
          title: "Colors",
          description: null,
          uri: "http://example.org/s1",
          top_concepts: ["c1", "c3"],
          concepts: {
            c1: makeConcept({
              pref_label: "Warm Colors",
              identifier: "warm",
              broader: [],
            }),
            c2: makeConcept({
              pref_label: "Red",
              identifier: "red",
              broader: ["c1"],
            }),
            c3: makeConcept({
              pref_label: "Blue",
              identifier: "blue",
              broader: [],
            }),
          },
        },
      ],
    });

    // No search: all nodes have matchStatus "none"
    searchMod.searchQuery.value = "";
    const noSearchTrees = searchMod.searchFilteredConceptTrees.value;
    const noSearchNodes = noSearchTrees.get("s1")!;
    expect(noSearchNodes[0].matchStatus).toBe("none");

    // Search for "Red": c2 should match, c1 should be ancestor, c3 should be none
    searchMod.searchQuery.value = "Red";
    const trees = searchMod.searchFilteredConceptTrees.value;
    const nodes = trees.get("s1")!;

    // Find nodes by label
    const blueNode = nodes.find((n) => n.label === "Blue");
    const warmNode = nodes.find((n) => n.label === "Warm Colors");

    expect(blueNode?.matchStatus).toBe("none");
    expect(warmNode?.matchStatus).toBe("ancestor");

    const redNode = warmNode?.children.find((n) => n.label === "Red");
    expect(redNode?.matchStatus).toBe("match");
  });

  it("expandMatchingPaths expands ancestor IDs", async () => {
    const vocabMod = await import("../../src/state/vocabulary");
    const searchMod = await import("../../src/state/search");
    const sidebarMod = await import("../../src/state/sidebar");

    sidebarMod.expandedIds.value = new Set();

    vocabMod.vocabulary.value = makeVocabulary({
      schemes: [
        {
          id: "s1",
          title: "Colors",
          description: null,
          uri: "http://example.org/s1",
          top_concepts: ["c1"],
          concepts: {
            c1: makeConcept({
              pref_label: "Warm",
              identifier: "warm",
              broader: [],
            }),
            c2: makeConcept({
              pref_label: "Red",
              identifier: "red",
              broader: ["c1"],
            }),
          },
        },
      ],
    });

    searchMod.expandMatchingPaths("red");

    // Should have expanded scheme s1 and ancestor c1
    expect(sidebarMod.expandedIds.value.has("s1")).toBe(true);
    expect(sidebarMod.expandedIds.value.has("c1")).toBe(true);
  });
});
