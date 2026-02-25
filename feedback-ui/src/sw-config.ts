/**
 * Service worker caching configuration.
 *
 * This file declares all caching strategies used by the service worker.
 * Every cached route and its strategy is defined here for visibility.
 */

export const CACHE_NAMES = {
  /** Immutable static assets (JS, CSS, fonts) */
  assets: "static-assets-v1",
  /** Published vocabulary files from blob storage */
  published: "published-v1",
} as const;

/** Max age in seconds for static asset cache entries */
export const ASSETS_CACHE_MAX_AGE_SECONDS = 30 * 24 * 60 * 60; // 30 days
