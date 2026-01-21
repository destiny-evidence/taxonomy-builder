import { describe, it, expect, beforeEach } from "vitest";
import {
  treeData,
  renderTree,
  draggedConceptId,
  getParentIdFromPath,
  isValidDropTarget,
  draggedDescendantIds,
} from "../../src/state/concepts";
import { searchQuery, hideNonMatches } from "../../src/state/search";
import type { TreeNode } from "../../src/types/models";

describe("renderTree", () => {
  beforeEach(() => {
    treeData.value = [];
    searchQuery.value = "";
    hideNonMatches.value = false;
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

  describe("search matchStatus", () => {
    it("all nodes have matchStatus 'none' when searchQuery is empty", () => {
      treeData.value = [
        createTreeNode("1", "Animals", [
          createTreeNode("2", "Dogs"),
        ]),
      ];
      searchQuery.value = "";

      const result = renderTree.value;

      expect(result[0].matchStatus).toBe("none");
      expect(result[0].children[0].matchStatus).toBe("none");
    });

    it("matching node has matchStatus 'match'", () => {
      treeData.value = [
        createTreeNode("1", "Animals", [
          createTreeNode("2", "Dogs"),
        ]),
      ];
      searchQuery.value = "dog";

      const result = renderTree.value;

      expect(result[0].children[0].matchStatus).toBe("match");
    });

    it("parent of matching node has matchStatus 'ancestor'", () => {
      treeData.value = [
        createTreeNode("1", "Animals", [
          createTreeNode("2", "Dogs"),
        ]),
      ];
      searchQuery.value = "dog";

      const result = renderTree.value;

      expect(result[0].matchStatus).toBe("ancestor");
    });

    it("non-matching node with no matching descendants has matchStatus 'none'", () => {
      treeData.value = [
        createTreeNode("mammals", "Mammals", [
          createTreeNode("dogs", "Dogs"),
        ]),
        createTreeNode("birds", "Birds", [
          createTreeNode("eagles", "Eagles"),
        ]),
      ];
      searchQuery.value = "dog";

      const result = renderTree.value;

      // Birds and Eagles don't match and have no matching descendants
      expect(result[1].matchStatus).toBe("none");
      expect(result[1].children[0].matchStatus).toBe("none");
    });

    it("matches against alt_labels", () => {
      treeData.value = [
        createTreeNodeWithAltLabels("1", "Canines", ["Dogs", "Puppies"]),
      ];
      searchQuery.value = "pupp";

      const result = renderTree.value;

      expect(result[0].matchStatus).toBe("match");
    });

    it("deeply nested match marks all ancestors", () => {
      treeData.value = [
        createTreeNode("1", "Animals", [
          createTreeNode("2", "Mammals", [
            createTreeNode("3", "Canines", [
              createTreeNode("4", "Dogs"),
            ]),
          ]),
        ]),
      ];
      searchQuery.value = "dog";

      const result = renderTree.value;

      expect(result[0].matchStatus).toBe("ancestor");
      expect(result[0].children[0].matchStatus).toBe("ancestor");
      expect(result[0].children[0].children[0].matchStatus).toBe("ancestor");
      expect(result[0].children[0].children[0].children[0].matchStatus).toBe("match");
    });
  });

  describe("hide non-matches filter", () => {
    it("includes all nodes when hideNonMatches is false", () => {
      treeData.value = [
        createTreeNode("mammals", "Mammals", [
          createTreeNode("dogs", "Dogs"),
        ]),
        createTreeNode("birds", "Birds"),
      ];
      searchQuery.value = "dog";
      hideNonMatches.value = false;

      const result = renderTree.value;

      expect(result).toHaveLength(2);
      expect(result[0].pref_label).toBe("Mammals");
      expect(result[1].pref_label).toBe("Birds");
    });

    it("excludes non-matching nodes when hideNonMatches is true", () => {
      treeData.value = [
        createTreeNode("mammals", "Mammals", [
          createTreeNode("dogs", "Dogs"),
        ]),
        createTreeNode("birds", "Birds"),
      ];
      searchQuery.value = "dog";
      hideNonMatches.value = true;

      const result = renderTree.value;

      expect(result).toHaveLength(1);
      expect(result[0].pref_label).toBe("Mammals");
    });

    it("preserves ancestors of matches when hiding", () => {
      treeData.value = [
        createTreeNode("animals", "Animals", [
          createTreeNode("mammals", "Mammals", [
            createTreeNode("dogs", "Dogs"),
            createTreeNode("cats", "Cats"),
          ]),
        ]),
      ];
      searchQuery.value = "dog";
      hideNonMatches.value = true;

      const result = renderTree.value;

      // Animals and Mammals should be kept as ancestors
      expect(result).toHaveLength(1);
      expect(result[0].pref_label).toBe("Animals");
      expect(result[0].children).toHaveLength(1);
      expect(result[0].children[0].pref_label).toBe("Mammals");
      // Cats should be filtered out, only Dogs remains
      expect(result[0].children[0].children).toHaveLength(1);
      expect(result[0].children[0].children[0].pref_label).toBe("Dogs");
    });

    it("shows all nodes when search is empty regardless of hideNonMatches", () => {
      treeData.value = [
        createTreeNode("mammals", "Mammals"),
        createTreeNode("birds", "Birds"),
      ];
      searchQuery.value = "";
      hideNonMatches.value = true;

      const result = renderTree.value;

      expect(result).toHaveLength(2);
    });
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

function createTreeNodeWithAltLabels(
  id: string,
  pref_label: string,
  alt_labels: string[],
  narrower: TreeNode[] = []
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

describe("drag and drop state", () => {
  beforeEach(() => {
    treeData.value = [];
    draggedConceptId.value = null;
  });

  describe("getParentIdFromPath", () => {
    it("returns null for root concepts", () => {
      expect(getParentIdFromPath("root-id")).toBeNull();
    });

    it("returns parent ID from path", () => {
      expect(getParentIdFromPath("parent-id/child-id")).toBe("parent-id");
    });

    it("returns immediate parent for deeply nested paths", () => {
      expect(getParentIdFromPath("grandparent/parent/child")).toBe("parent");
    });
  });

  describe("draggedDescendantIds", () => {
    it("returns empty set when not dragging", () => {
      treeData.value = [
        createTreeNode("root", "Root", [createTreeNode("child", "Child")]),
      ];

      expect(draggedDescendantIds.value.size).toBe(0);
    });

    it("collects all descendants of dragged node", () => {
      treeData.value = [
        createTreeNode("parent", "Parent", [
          createTreeNode("child", "Child", [
            createTreeNode("grandchild", "Grandchild"),
          ]),
        ]),
      ];

      draggedConceptId.value = "parent";

      const descendants = draggedDescendantIds.value;
      expect(descendants.has("child")).toBe(true);
      expect(descendants.has("grandchild")).toBe(true);
      expect(descendants.has("parent")).toBe(false);
    });

    it("handles multi-parent nodes correctly", () => {
      // Dogs appears under both Mammals and Pets
      treeData.value = [
        createTreeNode("mammals", "Mammals", [
          createTreeNode("dogs", "Dogs", [createTreeNode("puppies", "Puppies")]),
        ]),
        createTreeNode("pets", "Pets", [
          createTreeNode("dogs", "Dogs", [createTreeNode("puppies", "Puppies")]),
        ]),
      ];

      draggedConceptId.value = "mammals";

      const descendants = draggedDescendantIds.value;
      expect(descendants.has("dogs")).toBe(true);
      expect(descendants.has("puppies")).toBe(true);
    });
  });

  describe("isValidDropTarget", () => {
    beforeEach(() => {
      treeData.value = [
        createTreeNode("parent", "Parent", [
          createTreeNode("child", "Child", [
            createTreeNode("grandchild", "Grandchild"),
          ]),
        ]),
        createTreeNode("other", "Other"),
      ];
    });

    it("returns false when dropping on self", () => {
      draggedConceptId.value = "parent";
      expect(isValidDropTarget("parent", "parent", null)).toBe(false);
    });

    it("returns false when dropping on current parent", () => {
      draggedConceptId.value = "child";
      expect(isValidDropTarget("parent", "child", "parent")).toBe(false);
    });

    it("returns false when dropping on descendant", () => {
      draggedConceptId.value = "parent";
      expect(isValidDropTarget("grandchild", "parent", null)).toBe(false);
    });

    it("returns true for valid drop targets", () => {
      draggedConceptId.value = "child";
      expect(isValidDropTarget("other", "child", "parent")).toBe(true);
    });

    it("returns true when dropping on sibling", () => {
      treeData.value = [
        createTreeNode("parent", "Parent", [
          createTreeNode("child1", "Child 1"),
          createTreeNode("child2", "Child 2"),
        ]),
      ];
      draggedConceptId.value = "child1";
      expect(isValidDropTarget("child2", "child1", "parent")).toBe(true);
    });
  });
});
