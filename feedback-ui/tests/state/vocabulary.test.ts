import { describe, it, expect } from "vitest";

// Test the concept tree building logic by importing the module
// and setting up vocabulary state directly.
// We test the derived computation by assigning to the vocabulary signal.

describe("vocabulary state", () => {
  it("builds concept tree from flat concepts", async () => {
    // Import dynamically to avoid module-level side effects
    const mod = await import("../../src/state/vocabulary");

    mod.vocabulary.value = {
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
          title: "Scheme 1",
          description: null,
          uri: "http://example.org/s1",
          top_concepts: ["c1"],
          concepts: {
            c1: {
              pref_label: "Parent",
              identifier: "parent",
              uri: "http://example.org/c1",
              definition: null,
              scope_note: null,
              alt_labels: [],
              broader: [],
              related: [],
            },
            c2: {
              pref_label: "Child",
              identifier: "child",
              uri: "http://example.org/c2",
              definition: null,
              scope_note: null,
              alt_labels: [],
              broader: ["c1"],
              related: [],
            },
          },
        },
      ],
      classes: [],
      properties: [],
    };

    const trees = mod.conceptTrees.value;
    expect(trees.size).toBe(1);

    const tree = trees.get("s1")!;
    expect(tree).toHaveLength(1);
    expect(tree[0].label).toBe("Parent");
    expect(tree[0].children).toHaveLength(1);
    expect(tree[0].children[0].label).toBe("Child");
    expect(tree[0].children[0].children).toHaveLength(0);
  });

  it("infers top concepts when top_concepts is empty", async () => {
    const mod = await import("../../src/state/vocabulary");

    mod.vocabulary.value = {
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
          title: "Scheme 1",
          description: null,
          uri: "http://example.org/s1",
          top_concepts: [],
          concepts: {
            c1: {
              pref_label: "Root A",
              identifier: "a",
              uri: "http://example.org/a",
              definition: null,
              scope_note: null,
              alt_labels: [],
              broader: [],
              related: [],
            },
            c2: {
              pref_label: "Root B",
              identifier: "b",
              uri: "http://example.org/b",
              definition: null,
              scope_note: null,
              alt_labels: [],
              broader: [],
              related: [],
            },
          },
        },
      ],
      classes: [],
      properties: [],
    };

    const tree = mod.conceptTrees.value.get("s1")!;
    expect(tree).toHaveLength(2);
    const labels = tree.map((n) => n.label).sort();
    expect(labels).toEqual(["Root A", "Root B"]);
  });
});
