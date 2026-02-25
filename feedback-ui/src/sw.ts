/// <reference lib="webworker" />

import { precacheAndRoute } from "workbox-precaching";
import { registerRoute } from "workbox-routing";
import { NetworkFirst, CacheFirst } from "workbox-strategies";
import { ExpirationPlugin } from "workbox-expiration";
import { CACHE_NAMES, ASSETS_CACHE_MAX_AGE_SECONDS } from "./sw-config";

declare const self: ServiceWorkerGlobalScope;

// Precache the app shell. The manifest is injected by workbox-build tooling.
// Falls back to empty array when no injection step is configured.
precacheAndRoute(self.__WB_MANIFEST ?? []);

// ---------------------------------------------------------------------------
// Published taxonomy files (blob storage served via /published/*)
// ---------------------------------------------------------------------------

// Vocabulary files are immutable (versioned URL) — cache indefinitely
registerRoute(
  ({ url }) =>
    url.pathname.startsWith("/published/") &&
    url.pathname.endsWith("/vocabulary.json"),
  new CacheFirst({
    cacheName: CACHE_NAMES.published,
  })
);

// Index files are mutable (regenerated on publish) — network-first, no expiry
// so offline browsing works indefinitely after first load
registerRoute(
  ({ url }) =>
    url.pathname.startsWith("/published/") &&
    url.pathname.endsWith("/index.json"),
  new NetworkFirst({
    cacheName: CACHE_NAMES.published,
  })
);

// ---------------------------------------------------------------------------
// Static assets
// ---------------------------------------------------------------------------

// Cache-first (hashed filenames make them immutable)
registerRoute(
  ({ request }) =>
    request.destination === "script" ||
    request.destination === "style" ||
    request.destination === "font" ||
    request.destination === "image",
  new CacheFirst({
    cacheName: CACHE_NAMES.assets,
    plugins: [
      new ExpirationPlugin({
        maxAgeSeconds: ASSETS_CACHE_MAX_AGE_SECONDS,
      }),
    ],
  })
);
