import { describe, it, expect } from "vitest";
import { makeVocabulary, makeConcept } from "../fixtures";

describe("vocabulary state", () => {
  it("builds concept tree from flat concepts", async () => {
    const mod = await import("../../src/state/vocabulary");

    mod.vocabulary.value = makeVocabulary({
      schemes: [
        {
          id: "s1",
          title: "Scheme 1",
          description: null,
          uri: "http://example.org/s1",
          top_concepts: ["c1"],
          concepts: {
            c1: makeConcept({ pref_label: "Parent", identifier: "parent" }),
            c2: makeConcept({ pref_label: "Child", identifier: "child", broader: ["c1"] }),
          },
        },
      ],
    });

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

    mod.vocabulary.value = makeVocabulary({
      schemes: [
        {
          id: "s1",
          title: "Scheme 1",
          description: null,
          uri: "http://example.org/s1",
          top_concepts: [],
          concepts: {
            c1: makeConcept({ pref_label: "Root A", identifier: "a" }),
            c2: makeConcept({ pref_label: "Root B", identifier: "b" }),
          },
        },
      ],
    });

    const tree = mod.conceptTrees.value.get("s1")!;
    expect(tree).toHaveLength(2);
    const labels = tree.map((n) => n.label).sort();
    expect(labels).toEqual(["Root A", "Root B"]);
  });
});
