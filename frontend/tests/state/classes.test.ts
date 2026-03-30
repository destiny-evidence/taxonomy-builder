import { describe, it, expect, beforeEach } from "vitest";
import {
  ontologyClasses,
  selectedClassUri,
  selectedClass,
  creatingClass,
  classAncestors,
  isApplicable,
} from "../../src/state/classes";
import type { OntologyClass } from "../../src/types/models";

const mockClasses: OntologyClass[] = [
  {
    id: "1",
    project_id: "proj-1",
    identifier: "Investigation",
    uri: "http://example.org/Investigation",
    label: "Investigation",
    description: "A research effort",
    scope_note: null,
    superclass_uris: [],
    subclass_uris: [],
    restrictions: [],
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "2",
    project_id: "proj-1",
    identifier: "Finding",
    uri: "http://example.org/Finding",
    label: "Finding",
    description: "A specific result",
    scope_note: "Represents measured findings",
    superclass_uris: [],
    subclass_uris: [],
    restrictions: [],
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
  {
    id: "3",
    project_id: "proj-1",
    identifier: "Intervention",
    uri: "http://example.org/Intervention",
    label: "Intervention",
    description: null,
    scope_note: null,
    superclass_uris: [],
    subclass_uris: [],
    restrictions: [],
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-03T00:00:00Z",
  },
];

describe("classes state", () => {
  beforeEach(() => {
    ontologyClasses.value = [];
    selectedClassUri.value = null;
    creatingClass.value = null;
  });

  describe("signals", () => {
    it("ontologyClasses starts as empty array", () => {
      expect(ontologyClasses.value).toEqual([]);
    });

    it("selectedClassUri starts as null", () => {
      expect(selectedClassUri.value).toBeNull();
    });

    it("creatingClass starts as null", () => {
      expect(creatingClass.value).toBeNull();
    });
  });

  describe("ontologyClasses signal", () => {
    it("holds classes when set", () => {
      ontologyClasses.value = mockClasses;
      expect(ontologyClasses.value).toHaveLength(3);
      expect(ontologyClasses.value[0].label).toBe("Investigation");
    });
  });

  describe("creatingClass signal", () => {
    it("holds config when set", () => {
      creatingClass.value = { projectId: "proj-1" };
      expect(creatingClass.value).toEqual({ projectId: "proj-1" });
    });

    it("can be cleared", () => {
      creatingClass.value = { projectId: "proj-1" };
      creatingClass.value = null;
      expect(creatingClass.value).toBeNull();
    });
  });

  describe("selectedClass computed", () => {
    it("returns null when selectedClassUri is null", () => {
      ontologyClasses.value = mockClasses;
      expect(selectedClass.value).toBeNull();
    });

    it("returns null when classes are empty", () => {
      selectedClassUri.value = "http://example.org/Investigation";
      expect(selectedClass.value).toBeNull();
    });

    it("returns the selected class when both are set", () => {
      ontologyClasses.value = mockClasses;
      selectedClassUri.value = "http://example.org/Finding";
      expect(selectedClass.value).not.toBeNull();
      expect(selectedClass.value?.label).toBe("Finding");
    });

    it("returns null when URI doesn't match any class", () => {
      ontologyClasses.value = mockClasses;
      selectedClassUri.value = "http://example.org/NonExistent";
      expect(selectedClass.value).toBeNull();
    });
  });

  describe("classAncestors", () => {
    beforeEach(() => {
      ontologyClasses.value = [
        { uri: "ns/A", superclass_uris: [], subclass_uris: ["ns/B"], restrictions: [] },
        { uri: "ns/B", superclass_uris: ["ns/A"], subclass_uris: ["ns/C"], restrictions: [] },
        { uri: "ns/C", superclass_uris: ["ns/B"], subclass_uris: [], restrictions: [] },
      ] as any;
    });

    it("returns empty set for root class", () => {
      expect(classAncestors.value.get("ns/A")?.size).toBe(0);
    });

    it("returns direct parent for child", () => {
      expect(classAncestors.value.get("ns/B")).toEqual(new Set(["ns/A"]));
    });

    it("computes transitive ancestors", () => {
      expect(classAncestors.value.get("ns/C")).toEqual(new Set(["ns/A", "ns/B"]));
    });

    it("handles cycles gracefully", () => {
      ontologyClasses.value = [
        { uri: "ns/X", superclass_uris: ["ns/Y"], subclass_uris: [], restrictions: [] },
        { uri: "ns/Y", superclass_uris: ["ns/X"], subclass_uris: [], restrictions: [] },
      ] as any;
      expect(classAncestors.value.get("ns/X")).toEqual(new Set(["ns/Y"]));
      expect(classAncestors.value.get("ns/Y")).toEqual(new Set(["ns/X"]));
    });

    it("handles diamond inheritance", () => {
      ontologyClasses.value = [
        { uri: "ns/Top", superclass_uris: [], subclass_uris: ["ns/Left", "ns/Right"], restrictions: [] },
        { uri: "ns/Left", superclass_uris: ["ns/Top"], subclass_uris: ["ns/Bottom"], restrictions: [] },
        { uri: "ns/Right", superclass_uris: ["ns/Top"], subclass_uris: ["ns/Bottom"], restrictions: [] },
        { uri: "ns/Bottom", superclass_uris: ["ns/Left", "ns/Right"], subclass_uris: [], restrictions: [] },
      ] as any;
      expect(classAncestors.value.get("ns/Bottom")).toEqual(
        new Set(["ns/Left", "ns/Right", "ns/Top"])
      );
    });

    it("returns empty map when no classes loaded", () => {
      ontologyClasses.value = [];
      expect(classAncestors.value.size).toBe(0);
    });
  });

  describe("isApplicable", () => {
    beforeEach(() => {
      ontologyClasses.value = [
        { uri: "ns/A", superclass_uris: [], subclass_uris: ["ns/B"], restrictions: [] },
        { uri: "ns/B", superclass_uris: ["ns/A"], subclass_uris: [], restrictions: [] },
      ] as any;
    });

    it("returns true for direct domain match", () => {
      expect(isApplicable("ns/B", ["ns/B"])).toBe(true);
    });

    it("returns true when ancestor is in domain list", () => {
      expect(isApplicable("ns/B", ["ns/A"])).toBe(true);
    });

    it("returns false when class is not in domain and no ancestors match", () => {
      expect(isApplicable("ns/A", ["ns/B"])).toBe(false);
    });

    it("returns false for unknown class URI", () => {
      expect(isApplicable("ns/Unknown", ["ns/A"])).toBe(false);
    });

    it("returns false for empty domain list", () => {
      expect(isApplicable("ns/B", [])).toBe(false);
    });
  });
});
