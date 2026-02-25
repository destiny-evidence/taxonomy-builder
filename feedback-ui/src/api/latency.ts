import { signal } from "@preact/signals";

export const artificialLatency = signal(0);
export const bypassCache = signal(false);

export function delay(): Promise<void> {
  const ms = artificialLatency.value;
  if (ms <= 0) return Promise.resolve();
  return new Promise((r) => setTimeout(r, ms));
}

/** Return fetch RequestInit to bypass browser cache when active. */
export function cacheOptions(): RequestInit {
  return bypassCache.value ? { cache: "no-store" } : {};
}
