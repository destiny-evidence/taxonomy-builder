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

const ENTITY_KINDS = new Set<string>(["concept", "scheme", "class", "property"]);

function parsePath(p: string): Route {
  const segments = p.split("/").filter(Boolean);

  if (segments.length >= 4 && ENTITY_KINDS.has(segments[2])) {
    // /{projectId}/{version}/{entityKind}/{entityId}
    return {
      projectId: segments[0],
      version: segments[1],
      entityKind: segments[2] as EntityKind,
      entityId: segments.slice(3).join("/"),
    };
  }

  if (segments.length === 2) {
    // /{projectId}/{version}
    return { projectId: segments[0], version: segments[1], entityKind: null, entityId: null };
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

/** Navigate to a project version (no entity selected). */
export function navigateToProject(projectId: string, version: string): void {
  const path = `/${projectId}/${version}/`;
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
