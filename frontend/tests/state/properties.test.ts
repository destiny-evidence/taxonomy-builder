import { describe, it, expect, beforeEach } from "vitest";
import {
  properties,
  propertiesLoading,
  propertiesError,
  selectedPropertyId,
  selectedProperty,
  creatingProperty,
} from "../../src/state/properties";
import type { Property } from "../../src/types/models";

const mockProperty: Property = {
  id: "prop-1",
  project_id: "proj-1",
  identifier: "birthDate",
  label: "Birth Date",
  description: "Date of birth",
  domain_class: "http://example.org/Person",
  range_scheme_id: null,
  range_scheme: null,
  range_datatype: "xsd:date",
  range_class: null,
  cardinality: "single",
  required: false,
  uri: "http://example.org/birthDate",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("properties state", () => {
  beforeEach(() => {
    properties.value = [];
    propertiesLoading.value = false;
    propertiesError.value = null;
    selectedPropertyId.value = null;
    creatingProperty.value = null;
  });

  describe("properties signal", () => {
    it("starts with empty array", () => {
      expect(properties.value).toEqual([]);
    });

    it("can store property list", () => {
      properties.value = [mockProperty];
      expect(properties.value).toHaveLength(1);
      expect(properties.value[0].identifier).toBe("birthDate");
    });
  });

  describe("propertiesLoading signal", () => {
    it("starts as false", () => {
      expect(propertiesLoading.value).toBe(false);
    });

    it("can be set to true", () => {
      propertiesLoading.value = true;
      expect(propertiesLoading.value).toBe(true);
    });
  });

  describe("propertiesError signal", () => {
    it("starts as null", () => {
      expect(propertiesError.value).toBeNull();
    });

    it("can store error message", () => {
      propertiesError.value = "Failed to load properties";
      expect(propertiesError.value).toBe("Failed to load properties");
    });
  });

  describe("selectedProperty computed", () => {
    it("returns null when no property selected", () => {
      properties.value = [mockProperty];
      selectedPropertyId.value = null;
      expect(selectedProperty.value).toBeNull();
    });

    it("returns null when selected ID not in list", () => {
      properties.value = [mockProperty];
      selectedPropertyId.value = "nonexistent";
      expect(selectedProperty.value).toBeNull();
    });

    it("returns property when selected ID matches", () => {
      properties.value = [mockProperty];
      selectedPropertyId.value = "prop-1";
      expect(selectedProperty.value).toEqual(mockProperty);
    });

    it("updates when properties list changes", () => {
      selectedPropertyId.value = "prop-1";
      expect(selectedProperty.value).toBeNull();

      properties.value = [mockProperty];
      expect(selectedProperty.value).toEqual(mockProperty);
    });
  });

  describe("creatingProperty signal", () => {
    it("starts as null", () => {
      expect(creatingProperty.value).toBeNull();
    });

    it("can store create config with projectId and classUri", () => {
      creatingProperty.value = { projectId: "proj-1", domainClassUri: "http://example.org/Person" };
      expect(creatingProperty.value).toEqual({
        projectId: "proj-1",
        domainClassUri: "http://example.org/Person",
      });
    });
  });
});
