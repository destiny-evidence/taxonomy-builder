import { computed, signal } from "@preact/signals";

export type EntityKind = "concept" | "scheme" | "class" | "property";

export interface Route {
  projectId: string | null;
  version: string | null;
  entityKind: EntityKind | null;
  entityId: string | null;
}

const EMPTY_ROUTE: Route = { projectId: null, version: null, entityKind: null, entityId: null };

/** Raw pathname, updated on popstate and programmatic navigation. */
const pathname = signal(window.location.pathname);

function parsePath(p: string): Route {
  // Full entity route: /{projectId}/{version}/{entityKind}/{entityId}
  const full = p.match(/^\/([^/]+)\/([^/]+)\/(concept|scheme|class|property)\/(.+)$/);
  if (full) {
    return { projectId: full[1], version: full[2], entityKind: full[3] as EntityKind, entityId: full[4] };
  }
  // Project-only route: /{projectId}
  const projectOnly = p.match(/^\/([^/]+)$/);
  if (projectOnly) {
    return { projectId: projectOnly[1], version: null, entityKind: null, entityId: null };
  }
  return EMPTY_ROUTE;
}

/** Current parsed route, derived from pathname. */
export const route = computed(() => parsePath(pathname.value));

/** Navigate to an entity. */
export function navigate(projectId: string, version: string, entityKind: EntityKind, entityId: string): void {
  const path = `/${projectId}/${version}/${entityKind}/${entityId}`;
  history.pushState({}, "", path);
  pathname.value = path;
}

/** Navigate to a project (no entity selected). */
export function navigateToProject(projectId: string): void {
  const path = `/${projectId}`;
  history.pushState({}, "", path);
  pathname.value = path;
}

/** Navigate to root (clears entity selection, shows project list). */
export function navigateHome(): void {
  history.pushState({}, "", "/");
  pathname.value = "/";
}

function onPopState() {
  pathname.value = window.location.pathname;
}

export function initRouter(): void {
  pathname.value = window.location.pathname;
  window.addEventListener("popstate", onPopState);
}

export function destroyRouter(): void {
  window.removeEventListener("popstate", onPopState);
}
