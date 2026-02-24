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

// API responses: network-first with cache fallback
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

// Static assets: cache-first (hashed filenames make them immutable)
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
