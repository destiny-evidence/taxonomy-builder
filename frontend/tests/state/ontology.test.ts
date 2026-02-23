import { describe, it, expect, beforeEach } from "vitest";
import {
  ontologyClasses,
  selectedClassUri,
  selectedClass,
} from "../../src/state/ontology";
import type { OntologyClass } from "../../src/types/models";

const mockClasses: OntologyClass[] = [
  { id: "1", uri: "http://example.org/Investigation", label: "Investigation", description: "A research effort" },
  { id: "2", uri: "http://example.org/Finding", label: "Finding", description: "A specific result" },
  { id: "3", uri: "http://example.org/Intervention", label: "Intervention", description: null },
];

describe("ontology state", () => {
  beforeEach(() => {
    ontologyClasses.value = [];
    selectedClassUri.value = null;
  });

  describe("signals", () => {
    it("ontologyClasses starts as empty array", () => {
      expect(ontologyClasses.value).toEqual([]);
    });

    it("selectedClassUri starts as null", () => {
      expect(selectedClassUri.value).toBeNull();
    });
  });

  describe("ontologyClasses signal", () => {
    it("holds classes when set", () => {
      ontologyClasses.value = mockClasses;
      expect(ontologyClasses.value).toHaveLength(3);
      expect(ontologyClasses.value[0].label).toBe("Investigation");
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
