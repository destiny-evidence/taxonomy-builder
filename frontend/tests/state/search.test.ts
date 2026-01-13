import { describe, it, expect, beforeEach } from "vitest";
import {
  searchQuery,
  hideNonMatches,
  conceptMatchesSearch,
} from "../../src/state/search";

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

describe("conceptMatchesSearch", () => {
  it("matches pref_label case-insensitively", () => {
    expect(conceptMatchesSearch("Dogs", [], "dog")).toBe(true);
    expect(conceptMatchesSearch("Dogs", [], "DOG")).toBe(true);
    expect(conceptMatchesSearch("Dogs", [], "dogs")).toBe(true);
  });

  it("matches alt_labels case-insensitively", () => {
    expect(conceptMatchesSearch("Cats", ["Feline", "Kitty"], "kit")).toBe(true);
    expect(conceptMatchesSearch("Cats", ["Feline", "Kitty"], "feline")).toBe(true);
  });

  it("returns false when no match", () => {
    expect(conceptMatchesSearch("Birds", ["Avian"], "dog")).toBe(false);
  });

  it("matches partial strings", () => {
    expect(conceptMatchesSearch("Mammals", [], "mam")).toBe(true);
    expect(conceptMatchesSearch("Animals", ["Creatures"], "rea")).toBe(true);
  });

  it("returns true for empty query (matches everything)", () => {
    expect(conceptMatchesSearch("Anything", ["whatever"], "")).toBe(true);
  });

  it("handles empty alt_labels array", () => {
    expect(conceptMatchesSearch("Dogs", [], "dog")).toBe(true);
    expect(conceptMatchesSearch("Dogs", [], "cat")).toBe(false);
  });
});
