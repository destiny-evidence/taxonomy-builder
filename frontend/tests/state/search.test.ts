import { describe, it, expect, beforeEach } from "vitest";
import {
  searchQuery,
  hideNonMatches,
  conceptMatchesSearch,
  expandMatchingPaths,
} from "../../src/state/search";
import { treeData, expandedPaths } from "../../src/state/concepts";
import type { TreeNode } from "../../src/types/models";

describe("search state", () => {
  beforeEach(() => {
    searchQuery.value = "";
    hideNonMatches.value = false;
  });

  it("searchQuery defaults to empty string", () => {
    expect(searchQuery.value).toBe("");
  });

  it("hideNonMatches defaults to false", () => {
    expect(hideNonMatches.value).toBe(false);
  });

  it("searchQuery can be updated", () => {
    searchQuery.value = "dogs";
    expect(searchQuery.value).toBe("dogs");
  });

  it("hideNonMatches can be toggled", () => {
    hideNonMatches.value = true;
    expect(hideNonMatches.value).toBe(true);
  });
});

describe("conceptMatchesSearch", () => {
  it("matches pref_label case-insensitively", () => {
    expect(conceptMatchesSearch("Dogs", [], "dog")).toBe(true);
    expect(conceptMatchesSearch("Dogs", [], "DOG")).toBe(true);
    expect(conceptMatchesSearch("Dogs", [], "dogs")).toBe(true);
  });

  it("matches alt_labels case-insensitively", () => {
    expect(conceptMatchesSearch("Cats", ["Feline", "Kitty"], "kit")).toBe(true);
    expect(conceptMatchesSearch("Cats", ["Feline", "Kitty"], "feline")).toBe(true);
  });

  it("returns false when no match", () => {
    expect(conceptMatchesSearch("Birds", ["Avian"], "dog")).toBe(false);
  });

  it("matches partial strings", () => {
    expect(conceptMatchesSearch("Mammals", [], "mam")).toBe(true);
    expect(conceptMatchesSearch("Animals", ["Creatures"], "rea")).toBe(true);
  });

  it("returns true for empty query (matches everything)", () => {
    expect(conceptMatchesSearch("Anything", ["whatever"], "")).toBe(true);
  });

  it("handles empty alt_labels array", () => {
    expect(conceptMatchesSearch("Dogs", [], "dog")).toBe(true);
    expect(conceptMatchesSearch("Dogs", [], "cat")).toBe(false);
  });
});

// Helper to create TreeNode test data
function createTreeNode(
  id: string,
  pref_label: string,
  narrower: TreeNode[] = [],
  alt_labels: string[] = []
): TreeNode {
  return {
    id,
    scheme_id: "scheme-1",
    identifier: id,
    pref_label,
    definition: null,
    scope_note: null,
    uri: null,
    alt_labels,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    narrower,
  };
}

describe("expandMatchingPaths", () => {
  beforeEach(() => {
    treeData.value = [];
    expandedPaths.value = new Set();
    searchQuery.value = "";
  });

  it("expands paths to matching concepts", () => {
    treeData.value = [
      createTreeNode("animals", "Animals", [
        createTreeNode("mammals", "Mammals", [
          createTreeNode("dogs", "Dogs"),
        ]),
      ]),
    ];

    expandMatchingPaths("dog");

    expect(expandedPaths.value.has("animals")).toBe(true);
    expect(expandedPaths.value.has("animals/mammals")).toBe(true);
  });

  it("does not expand paths when no matches", () => {
    treeData.value = [
      createTreeNode("animals", "Animals", [
        createTreeNode("mammals", "Mammals"),
      ]),
    ];

    expandMatchingPaths("xyz");

    expect(expandedPaths.value.size).toBe(0);
  });

  it("preserves existing expanded paths", () => {
    treeData.value = [
      createTreeNode("animals", "Animals", [
        createTreeNode("mammals", "Mammals", [
          createTreeNode("dogs", "Dogs"),
        ]),
      ]),
      createTreeNode("plants", "Plants", [
        createTreeNode("trees", "Trees"),
      ]),
    ];
    expandedPaths.value = new Set(["plants"]);

    expandMatchingPaths("dog");

    expect(expandedPaths.value.has("plants")).toBe(true);
    expect(expandedPaths.value.has("animals")).toBe(true);
    expect(expandedPaths.value.has("animals/mammals")).toBe(true);
  });

  it("does nothing for empty query", () => {
    treeData.value = [
      createTreeNode("animals", "Animals", [
        createTreeNode("dogs", "Dogs"),
      ]),
    ];

    expandMatchingPaths("");

    expect(expandedPaths.value.size).toBe(0);
  });
});
