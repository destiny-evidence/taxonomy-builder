import { describe, it, expect } from "vitest";
import {
  CACHE_NAMES,
  API_CACHE_MAX_AGE_SECONDS,
  API_CACHE_MAX_ENTRIES,
  ASSETS_CACHE_MAX_AGE_SECONDS,
} from "../src/sw-config";

describe("sw-config", () => {
  it("defines unique cache names", () => {
    const names = Object.values(CACHE_NAMES);
    expect(new Set(names).size).toBe(names.length);
  });

  it("cache names include version suffix", () => {
    for (const name of Object.values(CACHE_NAMES)) {
      expect(name).toMatch(/-v\d+$/);
    }
  });

  it("API cache max age is positive", () => {
    expect(API_CACHE_MAX_AGE_SECONDS).toBeGreaterThan(0);
  });

  it("API cache max entries is positive", () => {
    expect(API_CACHE_MAX_ENTRIES).toBeGreaterThan(0);
  });

  it("assets cache max age is at least 1 day", () => {
    expect(ASSETS_CACHE_MAX_AGE_SECONDS).toBeGreaterThanOrEqual(86400);
  });
});
