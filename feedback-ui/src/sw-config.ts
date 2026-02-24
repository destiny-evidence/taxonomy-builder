/**
 * Service worker caching configuration.
 *
 * This file declares all caching strategies used by the service worker.
 * Every cached route and its strategy is defined here for visibility.
 */

export const CACHE_NAMES = {
  /** Cached API responses for feedback data */
  api: "feedback-api-v1",
  /** Immutable static assets (JS, CSS, fonts) */
  assets: "static-assets-v1",
  /** Published vocabulary files from blob storage */
  published: "published-v1",
} as const;

/** Max age in seconds for API cache entries */
export const API_CACHE_MAX_AGE_SECONDS = 300;

/** Max number of entries in the API cache */
export const API_CACHE_MAX_ENTRIES = 50;

/** Max age in seconds for static asset cache entries */
export const ASSETS_CACHE_MAX_AGE_SECONDS = 30 * 24 * 60 * 60; // 30 days
