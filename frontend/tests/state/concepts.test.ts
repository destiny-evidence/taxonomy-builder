import { describe, it, expect, beforeEach } from "vitest";
import { treeData, renderTree } from "../../src/state/concepts";
import type { TreeNode } from "../../src/types/models";

describe("renderTree", () => {
  beforeEach(() => {
    treeData.value = [];
  });

  it("returns empty array for empty tree", () => {
    treeData.value = [];
    expect(renderTree.value).toEqual([]);
  });

  it("handles flat concepts with no hierarchy", () => {
    treeData.value = [
      createTreeNode("1", "Animals"),
      createTreeNode("2", "Plants"),
    ];

    const result = renderTree.value;

    expect(result).toHaveLength(2);
    expect(result[0].pref_label).toBe("Animals");
    expect(result[0].depth).toBe(0);
    expect(result[0].children).toEqual([]);
    expect(result[1].pref_label).toBe("Plants");
  });

  it("builds simple hierarchy with correct depth", () => {
    treeData.value = [
      createTreeNode("1", "Animals", [
        createTreeNode("2", "Mammals", [
          createTreeNode("3", "Dogs"),
        ]),
      ]),
    ];

    const result = renderTree.value;

    expect(result).toHaveLength(1);
    expect(result[0].depth).toBe(0);
    expect(result[0].children).toHaveLength(1);
    expect(result[0].children[0].depth).toBe(1);
    expect(result[0].children[0].children).toHaveLength(1);
    expect(result[0].children[0].children[0].depth).toBe(2);
  });

  it("constructs paths correctly", () => {
    treeData.value = [
      createTreeNode("root", "Animals", [
        createTreeNode("child", "Mammals", [
          createTreeNode("grandchild", "Dogs"),
        ]),
      ]),
    ];

    const result = renderTree.value;

    expect(result[0].path).toBe("root");
    expect(result[0].children[0].path).toBe("root/child");
    expect(result[0].children[0].children[0].path).toBe("root/child/grandchild");
  });

  it("detects multi-parent concepts (polyhierarchy)", () => {
    // Dogs appears under both Mammals and Pets
    treeData.value = [
      createTreeNode("mammals", "Mammals", [
        createTreeNode("dogs", "Dogs"),
      ]),
      createTreeNode("pets", "Pets", [
        createTreeNode("dogs", "Dogs"),
      ]),
    ];

    const result = renderTree.value;

    // Find Dogs under Mammals
    const dogsUnderMammals = result[0].children[0];
    expect(dogsUnderMammals.hasMultipleParents).toBe(true);
    expect(dogsUnderMammals.otherParentLabels).toContain("Pets");

    // Find Dogs under Pets
    const dogsUnderPets = result[1].children[0];
    expect(dogsUnderPets.hasMultipleParents).toBe(true);
    expect(dogsUnderPets.otherParentLabels).toContain("Mammals");
  });

  it("excludes current parent from otherParentLabels", () => {
    treeData.value = [
      createTreeNode("mammals", "Mammals", [
        createTreeNode("dogs", "Dogs"),
      ]),
      createTreeNode("pets", "Pets", [
        createTreeNode("dogs", "Dogs"),
      ]),
    ];

    const result = renderTree.value;

    // Dogs under Mammals should NOT show "Mammals" in otherParentLabels
    const dogsUnderMammals = result[0].children[0];
    expect(dogsUnderMammals.otherParentLabels).not.toContain("Mammals");

    // Dogs under Pets should NOT show "Pets" in otherParentLabels
    const dogsUnderPets = result[1].children[0];
    expect(dogsUnderPets.otherParentLabels).not.toContain("Pets");
  });

  it("single-parent concepts have hasMultipleParents false", () => {
    treeData.value = [
      createTreeNode("mammals", "Mammals", [
        createTreeNode("dogs", "Dogs"),
      ]),
    ];

    const result = renderTree.value;

    expect(result[0].hasMultipleParents).toBe(false);
    expect(result[0].children[0].hasMultipleParents).toBe(false);
  });

  it("root concepts have empty otherParentLabels", () => {
    treeData.value = [
      createTreeNode("root", "Animals"),
    ];

    const result = renderTree.value;

    expect(result[0].otherParentLabels).toEqual([]);
  });

  it("preserves definition from source node", () => {
    treeData.value = [
      createTreeNode("1", "Animals", [], "Living organisms"),
    ];

    const result = renderTree.value;

    expect(result[0].definition).toBe("Living organisms");
  });
});

// Helper to create TreeNode test data
function createTreeNode(
  id: string,
  pref_label: string,
  narrower: TreeNode[] = [],
  definition: string | null = null
): TreeNode {
  return {
    id,
    scheme_id: "scheme-1",
    identifier: id,
    pref_label,
    definition,
    scope_note: null,
    uri: null,
    alt_labels: [],
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    narrower,
  };
}
