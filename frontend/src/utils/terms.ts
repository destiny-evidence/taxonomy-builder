import type { Project } from "../types/models";

type ProjectNamespaces = Pick<Project, "namespace" | "namespace_prefixes">;

function isProjectTerm(uri: string, project: ProjectNamespaces): boolean {
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

/** Label with its external prefix, for plain-text contexts such as <option>. */
export function prefixedLabel(uri: string, label: string, project: ProjectNamespaces | null): string {
  const prefix = externalPrefix(uri, project);
  return prefix ? `${prefix} ${label}` : label;
}
