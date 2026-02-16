import { describe, it, expect } from "vitest";
import {
  HISTORY_FILTERS,
  getAllowedEntityTypes,
} from "../../../src/components/history/historyFilters";

describe("HISTORY_FILTERS", () => {
  it("defines all five filter categories", () => {
    const keys = HISTORY_FILTERS.map((f) => f.key);
    expect(keys).toEqual([
      "concepts",
      "schemes",
      "properties",
      "relationships",
      "project",
    ]);
  });

  it("maps relationships to both broader and related entity types", () => {
    const rel = HISTORY_FILTERS.find((f) => f.key === "relationships");
    expect(rel?.types).toEqual(["concept_broader", "concept_related"]);
  });
});

describe("getAllowedEntityTypes", () => {
  it("returns null when no filters selected (show all)", () => {
    expect(getAllowedEntityTypes(new Set())).toBeNull();
  });

  it("returns matching entity types for a single filter", () => {
    const result = getAllowedEntityTypes(new Set(["concepts"]));
    expect(result).toEqual(new Set(["concept"]));
  });

  it("returns both entity types for relationships filter", () => {
    const result = getAllowedEntityTypes(new Set(["relationships"]));
    expect(result).toEqual(new Set(["concept_broader", "concept_related"]));
  });

  it("returns union of entity types for multiple filters", () => {
    const result = getAllowedEntityTypes(new Set(["concepts", "properties"]));
    expect(result).toEqual(new Set(["concept", "property"]));
  });
});
