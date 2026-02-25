import { computed, signal } from "@preact/signals";

export type EntityKind = "concept" | "scheme" | "class" | "property";

export interface Route {
  projectId: string | null;
  version: string | null;
  entityKind: EntityKind | null;
  entityId: string | null;
}

const EMPTY_ROUTE: Route = { projectId: null, version: null, entityKind: null, entityId: null };

/** Strip Keycloak callback params that leak into the hash after login redirect. */
function cleanHash(raw: string): string {
  return raw.split("&")[0];
}

/** Raw hash string (without leading #), updated on hashchange. */
const hash = signal(cleanHash(window.location.hash.slice(1)));

function parseHash(h: string): Route {
  // Full entity route: /{projectId}/{version}/{entityKind}/{entityId}
  const full = h.match(/^\/([^/]+)\/([^/]+)\/(concept|scheme|class|property)\/(.+)$/);
  if (full) {
    return { projectId: full[1], version: full[2], entityKind: full[3] as EntityKind, entityId: full[4] };
  }
  // Project-only route: /{projectId}
  const projectOnly = h.match(/^\/([^/]+)$/);
  if (projectOnly) {
    return { projectId: projectOnly[1], version: null, entityKind: null, entityId: null };
  }
  return EMPTY_ROUTE;
}

/** Current parsed route, derived from hash. */
export const route = computed(() => parseHash(hash.value));

/** Navigate to an entity by updating the hash. */
export function navigate(projectId: string, version: string, entityKind: EntityKind, entityId: string): void {
  window.location.hash = `/${projectId}/${version}/${entityKind}/${entityId}`;
}

/** Navigate to a project (no entity selected). */
export function navigateToProject(projectId: string): void {
  window.location.hash = `/${projectId}`;
}

/** Navigate to root (clears entity selection, shows project list). */
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
