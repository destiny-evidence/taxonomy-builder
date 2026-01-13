import { describe, it, expect, beforeEach } from "vitest";
import { searchQuery, hideNonMatches } from "../../src/state/search";

describe("search state", () => {
  beforeEach(() => {
    searchQuery.value = "";
    hideNonMatches.value = false;
  });

  it("searchQuery defaults to empty string", () => {
    expect(searchQuery.value).toBe("");
  });

  it("hideNonMatches defaults to false", () => {
    expect(hideNonMatches.value).toBe(false);
  });

  it("searchQuery can be updated", () => {
    searchQuery.value = "dogs";
    expect(searchQuery.value).toBe("dogs");
  });

  it("hideNonMatches can be toggled", () => {
    hideNonMatches.value = true;
    expect(hideNonMatches.value).toBe(true);
  });
});
