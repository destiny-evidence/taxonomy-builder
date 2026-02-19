import { describe, it, expect, beforeEach } from "vitest";
import {
  ontology,
  ontologyLoading,
  ontologyError,
  ontologyClasses,
  selectedClassUri,
  selectedClass,
} from "../../src/state/ontology";
import type { CoreOntology } from "../../src/types/models";

const mockOntology: CoreOntology = {
  classes: [
    { uri: "http://example.org/Investigation", label: "Investigation", comment: "A research effort" },
    { uri: "http://example.org/Finding", label: "Finding", comment: "A specific result" },
    { uri: "http://example.org/Intervention", label: "Intervention", comment: null },
  ],
  object_properties: [],
  datatype_properties: [],
};

describe("ontology state", () => {
  beforeEach(() => {
    ontology.value = null;
    ontologyLoading.value = false;
    ontologyError.value = null;
    selectedClassUri.value = null;
  });

  describe("signals", () => {
    it("ontology starts as null", () => {
      expect(ontology.value).toBeNull();
    });

    it("ontologyLoading starts as false", () => {
      expect(ontologyLoading.value).toBe(false);
    });

    it("ontologyError starts as null", () => {
      expect(ontologyError.value).toBeNull();
    });

    it("selectedClassUri starts as null", () => {
      expect(selectedClassUri.value).toBeNull();
    });
  });

  describe("ontologyClasses computed", () => {
    it("returns empty array when ontology is null", () => {
      expect(ontologyClasses.value).toEqual([]);
    });

    it("returns classes when ontology is loaded", () => {
      ontology.value = mockOntology;
      expect(ontologyClasses.value).toHaveLength(3);
      expect(ontologyClasses.value[0].label).toBe("Investigation");
    });
  });

  describe("selectedClass computed", () => {
    it("returns null when selectedClassUri is null", () => {
      ontology.value = mockOntology;
      expect(selectedClass.value).toBeNull();
    });

    it("returns null when ontology is null", () => {
      selectedClassUri.value = "http://example.org/Investigation";
      expect(selectedClass.value).toBeNull();
    });

    it("returns the selected class when both are set", () => {
      ontology.value = mockOntology;
      selectedClassUri.value = "http://example.org/Finding";
      expect(selectedClass.value).not.toBeNull();
      expect(selectedClass.value?.label).toBe("Finding");
    });

    it("returns null when URI doesn't match any class", () => {
      ontology.value = mockOntology;
      selectedClassUri.value = "http://example.org/NonExistent";
      expect(selectedClass.value).toBeNull();
    });
  });
});
