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

  if (segments.length === 1) {
    // /{projectId} — versionless, resolved by AppShell
    return { projectId: segments[0], version: null, entityKind: null, entityId: null };
  }

  return EMPTY_ROUTE;
}

/** Current parsed route, derived from pathname. */
export const route = computed(() => parsePath(pathname.value));

/**
 * On mobile, only one pane is visible at a time.
 * "sidebar" = navigation list, "detail" = entity/welcome panel.
 * On desktop this signal is ignored (both panes always visible).
 */
export const mobileView = signal<"sidebar" | "detail">("sidebar");

function syncMobileView(r: Route): void {
  mobileView.value = r.entityId ? "detail" : "sidebar";
}

/** Navigate to an entity. */
export function navigate(projectId: string, version: string, entityKind: EntityKind, entityId: string): void {
  const path = `/${projectId}/${version}/${entityKind}/${entityId}`;
  navDepth++;
  history.pushState({}, "", path);
  pathname.value = path;
  mobileView.value = "detail";
}

/** Navigate to a project version (no entity selected). */
export function navigateToProject(projectId: string, version: string, { replace = false } = {}): void {
  const path = `/${projectId}/${version}/`;
  if (replace) {
    history.replaceState({}, "", path);
  } else {
    navDepth++;
    history.pushState({}, "", path);
  }
  pathname.value = path;
}

/** Navigate to a project without a version (triggers version resolution). */
export function navigateToProjectLatest(projectId: string): void {
  const path = `/${projectId}/`;
  navDepth++;
  history.pushState({}, "", path);
  pathname.value = path;
}

/** Navigate to root (clears entity selection, shows project list). */
export function navigateHome(): void {
  navDepth++;
  history.pushState({}, "", "/");
  pathname.value = "/";
}

/** Track in-app navigation depth so we know if history.back() is safe. */
let navDepth = 0;

/** Go back one step in browser history, or return false if there's no in-app history. */
export function goBack(): boolean {
  if (navDepth > 0) {
    navDepth--;
    history.back();
    return true;
  }
  return false;
}

function onPopState() {
  pathname.value = window.location.pathname;
  syncMobileView(parsePath(pathname.value));
}

export function initRouter(): void {
  navDepth = 0;
  pathname.value = window.location.pathname;
  syncMobileView(parsePath(pathname.value));
  window.addEventListener("popstate", onPopState);
}

export function destroyRouter(): void {
  window.removeEventListener("popstate", onPopState);
}
