import { describe, it, expect, beforeEach } from "vitest";
import { viewMode, graphData } from "../../src/state/graph";
import { concepts } from "../../src/state/concepts";
import { makeConcept } from "../helpers/factories";

describe("graph state", () => {
  beforeEach(() => {
    viewMode.value = "tree";
    concepts.value = [];
  });

  describe("viewMode", () => {
    it("defaults to tree", () => {
      expect(viewMode.value).toBe("tree");
    });

    it("can be set to graph", () => {
      viewMode.value = "graph";
      expect(viewMode.value).toBe("graph");
    });
  });

  describe("graphData", () => {
    it("returns empty nodes and edges when concepts is empty", () => {
      const data = graphData.value;
      expect(data.nodes).toEqual([]);
      expect(data.edges).toEqual([]);
    });

    it("creates a node for each concept", () => {
      concepts.value = [
        makeConcept({ id: "a", pref_label: "Alpha", definition: "First" }),
        makeConcept({ id: "b", pref_label: "Beta" }),
      ];

      const { nodes } = graphData.value;
      expect(nodes).toHaveLength(2);
      expect(nodes[0]).toMatchObject({ id: "a", label: "Alpha", definition: "First", isRoot: true });
      expect(nodes[1]).toMatchObject({ id: "b", label: "Beta", definition: null, isRoot: true });
    });

    it("marks concepts with broader as non-root", () => {
      const parent = makeConcept({ id: "parent", pref_label: "Parent" });
      const child = makeConcept({
        id: "child",
        pref_label: "Child",
        broader: [{ id: "parent", pref_label: "Parent", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" }],
      });
      concepts.value = [parent, child];

      const { nodes } = graphData.value;
      const parentNode = nodes.find((n) => n.id === "parent");
      const childNode = nodes.find((n) => n.id === "child");
      expect(parentNode!.isRoot).toBe(true);
      expect(childNode!.isRoot).toBe(false);
    });

    it("creates broader edges", () => {
      concepts.value = [
        makeConcept({ id: "parent", pref_label: "Parent" }),
        makeConcept({
          id: "child",
          pref_label: "Child",
          broader: [{ id: "parent", pref_label: "Parent", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" }],
        }),
      ];

      const { edges } = graphData.value;
      expect(edges).toHaveLength(1);
      expect(edges[0]).toEqual({ source: "child", target: "parent", type: "broader" });
    });

    it("creates broader edges for polyhierarchy (multiple parents)", () => {
      concepts.value = [
        makeConcept({ id: "p1", pref_label: "Parent 1" }),
        makeConcept({ id: "p2", pref_label: "Parent 2" }),
        makeConcept({
          id: "child",
          pref_label: "Child",
          broader: [
            { id: "p1", pref_label: "Parent 1", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" },
            { id: "p2", pref_label: "Parent 2", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" },
          ],
        }),
      ];

      const { edges } = graphData.value;
      const broaderEdges = edges.filter((e) => e.type === "broader");
      expect(broaderEdges).toHaveLength(2);
      expect(broaderEdges).toContainEqual({ source: "child", target: "p1", type: "broader" });
      expect(broaderEdges).toContainEqual({ source: "child", target: "p2", type: "broader" });
    });

    it("creates related edges", () => {
      concepts.value = [
        makeConcept({
          id: "a",
          pref_label: "Alpha",
          related: [{ id: "b", pref_label: "Beta", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" }],
        }),
        makeConcept({
          id: "b",
          pref_label: "Beta",
          related: [{ id: "a", pref_label: "Alpha", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" }],
        }),
      ];

      const { edges } = graphData.value;
      const relatedEdges = edges.filter((e) => e.type === "related");
      // Should be deduplicated: A-related-B and B-related-A = one edge
      expect(relatedEdges).toHaveLength(1);
      expect(relatedEdges[0].type).toBe("related");
      // The edge should contain both IDs (order doesn't matter)
      const ids = [relatedEdges[0].source, relatedEdges[0].target].sort();
      expect(ids).toEqual(["a", "b"]);
    });

    it("deduplicates related edges across concepts", () => {
      concepts.value = [
        makeConcept({
          id: "a",
          pref_label: "Alpha",
          related: [
            { id: "b", pref_label: "Beta", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" },
            { id: "c", pref_label: "Gamma", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" },
          ],
        }),
        makeConcept({
          id: "b",
          pref_label: "Beta",
          related: [{ id: "a", pref_label: "Alpha", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" }],
        }),
        makeConcept({ id: "c", pref_label: "Gamma" }),
      ];

      const { edges } = graphData.value;
      const relatedEdges = edges.filter((e) => e.type === "related");
      // a-b appears twice (from a and from b), a-c appears once -> 2 unique edges
      expect(relatedEdges).toHaveLength(2);
    });

    it("combines broader and related edges", () => {
      concepts.value = [
        makeConcept({ id: "parent", pref_label: "Parent" }),
        makeConcept({
          id: "child",
          pref_label: "Child",
          broader: [{ id: "parent", pref_label: "Parent", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" }],
          related: [{ id: "sibling", pref_label: "Sibling", scheme_id: "scheme-1", identifier: null, definition: null, scope_note: null, uri: null, alt_labels: [], created_at: "", updated_at: "" }],
        }),
        makeConcept({ id: "sibling", pref_label: "Sibling" }),
      ];

      const { edges } = graphData.value;
      expect(edges).toHaveLength(2);
      expect(edges.filter((e) => e.type === "broader")).toHaveLength(1);
      expect(edges.filter((e) => e.type === "related")).toHaveLength(1);
    });
  });
});
