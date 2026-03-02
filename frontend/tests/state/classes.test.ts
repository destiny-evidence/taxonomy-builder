import { describe, it, expect, beforeEach } from "vitest";
import {
  ontologyClasses,
  selectedClassUri,
  selectedClass,
  creatingClass,
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
});
