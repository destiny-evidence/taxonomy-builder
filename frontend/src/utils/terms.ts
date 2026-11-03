import type { Project } from "../types/models";

type ProjectNamespaces = Pick<Project, "namespace" | "namespace_prefixes">;

function isProjectTerm(uri: string, project: ProjectNamespaces): boolean {
  // Mirrors the backend's namespace normalisation in context generation.
  return uri.startsWith(project.namespace.replace(/\/+$/, "") + "/");
}

function boundPrefix(uri: string, project: ProjectNamespaces): [string, string] | null {
  let best: [string, string] | null = null;
  for (const [prefix, namespace] of Object.entries(project.namespace_prefixes)) {
    if (prefix && uri.startsWith(namespace) && (!best || namespace.length > best[1].length)) {
      best = [prefix, namespace];
    }
  }
  return best;
}

/**
 * Prefix distinguishing a term from another vocabulary: its bound prefix
 * (e.g. "gn"), or its namespace when none is bound. Null for project terms.
 */
export function externalPrefix(uri: string, project: ProjectNamespaces | null): string | null {
  if (!project || isProjectTerm(uri, project)) return null;
  const bound = boundPrefix(uri, project);
  if (bound) return bound[0];
  return uri.slice(0, Math.max(uri.lastIndexOf("#"), uri.lastIndexOf("/")) + 1);
}
