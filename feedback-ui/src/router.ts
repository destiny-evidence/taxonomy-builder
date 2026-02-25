import { computed, signal } from "@preact/signals";

export type EntityKind = "concept" | "scheme" | "class" | "property";

export interface Route {
  version: string | null;
  entityKind: EntityKind | null;
  entityId: string | null;
}

const EMPTY_ROUTE: Route = { version: null, entityKind: null, entityId: null };

/** Strip Keycloak callback params that leak into the hash after login redirect. */
function cleanHash(raw: string): string {
  return raw.split("&")[0];
}

/** Raw hash string (without leading #), updated on hashchange. */
const hash = signal(cleanHash(window.location.hash.slice(1)));

function parseHash(h: string): Route {
  // #/{version}/{entityKind}/{entityId}
  const match = h.match(/^\/([^/]+)\/(concept|scheme|class|property)\/(.+)$/);
  if (match) {
    return { version: match[1], entityKind: match[2] as EntityKind, entityId: match[3] };
  }
  return EMPTY_ROUTE;
}

/** Current parsed route, derived from hash. */
export const route = computed(() => parseHash(hash.value));

/** Navigate by updating the hash. */
export function navigate(version: string, entityKind: EntityKind, entityId: string): void {
  window.location.hash = `/${version}/${entityKind}/${entityId}`;
}

/** Navigate to root (clears entity selection). */
export function navigateHome(): void {
  window.location.hash = "";
}

function onHashChange() {
  hash.value = cleanHash(window.location.hash.slice(1));
}

export function initRouter(): void {
  window.addEventListener("hashchange", onHashChange);
}

export function destroyRouter(): void {
  window.removeEventListener("hashchange", onHashChange);
}
