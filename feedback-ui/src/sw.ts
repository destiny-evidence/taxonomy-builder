/// <reference lib="webworker" />

import { precacheAndRoute } from "workbox-precaching";
import { registerRoute } from "workbox-routing";
import { NetworkFirst, CacheFirst } from "workbox-strategies";
import { ExpirationPlugin } from "workbox-expiration";
import {
  CACHE_NAMES,
  API_CACHE_MAX_AGE_SECONDS,
  API_CACHE_MAX_ENTRIES,
  ASSETS_CACHE_MAX_AGE_SECONDS,
} from "./sw-config";

declare const self: ServiceWorkerGlobalScope;

// Precache the app shell. The manifest is injected by workbox-build tooling.
// Falls back to empty array when no injection step is configured.
precacheAndRoute(self.__WB_MANIFEST ?? []);

// ---------------------------------------------------------------------------
// Feedback API
// ---------------------------------------------------------------------------

// GET: network-first with cache fallback
registerRoute(
  ({ url }) => url.pathname.startsWith("/api/feedback/"),
  new NetworkFirst({
    cacheName: CACHE_NAMES.api,
    plugins: [
      new ExpirationPlugin({
        maxEntries: API_CACHE_MAX_ENTRIES,
        maxAgeSeconds: API_CACHE_MAX_AGE_SECONDS,
      }),
    ],
  })
);

// POST / DELETE: forward to network, then refresh the GET cache so the UI
// has fresh data immediately (even if the user goes offline right after).
for (const method of ["POST", "DELETE"] as const) {
  registerRoute(
    ({ url }) => url.pathname.startsWith("/api/feedback/"),
    {
      handle: async ({ request, url }) => {
        const response = await fetch(request);
        if (response.ok) {
          const cache = await caches.open(CACHE_NAMES.api);
          try {
            const fresh = await fetch(url.href);
            if (fresh.ok) await cache.put(url.href, fresh);
          } catch {
            // offline — GET cache will refresh next time
          }
        }
        return response;
      },
    },
    method
  );
}

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
    request.destination === "font",
  new CacheFirst({
    cacheName: CACHE_NAMES.assets,
    plugins: [
      new ExpirationPlugin({
        maxAgeSeconds: ASSETS_CACHE_MAX_AGE_SECONDS,
      }),
    ],
  })
);
