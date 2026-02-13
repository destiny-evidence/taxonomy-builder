import { describe, it, expect, beforeEach } from "vitest";
import {
  selectionMode,
  isClassMode,
  isSchemeMode,
} from "../../src/state/workspace";

describe("workspace state", () => {
  beforeEach(() => {
    selectionMode.value = null;
  });

  describe("selectionMode", () => {
    it("defaults to null", () => {
      expect(selectionMode.value).toBe(null);
    });

    it("can be set to class", () => {
      selectionMode.value = "class";
      expect(selectionMode.value).toBe("class");
    });

    it("can be set to scheme", () => {
      selectionMode.value = "scheme";
      expect(selectionMode.value).toBe("scheme");
    });

    it("can be reset to null", () => {
      selectionMode.value = "class";
      selectionMode.value = null;
      expect(selectionMode.value).toBe(null);
    });
  });

  describe("isClassMode", () => {
    it("returns false when selectionMode is null", () => {
      selectionMode.value = null;
      expect(isClassMode.value).toBe(false);
    });

    it("returns true when selectionMode is class", () => {
      selectionMode.value = "class";
      expect(isClassMode.value).toBe(true);
    });

    it("returns false when selectionMode is scheme", () => {
      selectionMode.value = "scheme";
      expect(isClassMode.value).toBe(false);
    });
  });

  describe("isSchemeMode", () => {
    it("returns false when selectionMode is null", () => {
      selectionMode.value = null;
      expect(isSchemeMode.value).toBe(false);
    });

    it("returns false when selectionMode is class", () => {
      selectionMode.value = "class";
      expect(isSchemeMode.value).toBe(false);
    });

    it("returns true when selectionMode is scheme", () => {
      selectionMode.value = "scheme";
      expect(isSchemeMode.value).toBe(true);
    });
  });
});
