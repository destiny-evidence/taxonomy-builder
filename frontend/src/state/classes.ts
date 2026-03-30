import { signal, computed } from "@preact/signals";
import type { OntologyClass } from "../types/models";

export const ontologyClasses = signal<OntologyClass[]>([]);
export const selectedClassUri = signal<string | null>(null);

export interface CreatingClassConfig {
  projectId: string;
}

export const creatingClass = signal<CreatingClassConfig | null>(null);

export const selectedClass = computed<OntologyClass | null>(() => {
  if (!selectedClassUri.value) return null;
  return ontologyClasses.value.find((c) => c.uri === selectedClassUri.value) ?? null;
});

/** Transitive ancestor map: class URI → set of all ancestor URIs (BFS, cycle-safe). */
export const classAncestors = computed<Map<string, Set<string>>>(() => {
  const classes = ontologyClasses.value;
  const uriToSuperclasses = new Map<string, string[]>();
  for (const cls of classes) {
    uriToSuperclasses.set(cls.uri, cls.superclass_uris);
  }

  const result = new Map<string, Set<string>>();
  for (const cls of classes) {
    const ancestors = new Set<string>();
    const queue = [...cls.superclass_uris];
    while (queue.length > 0) {
      const uri = queue.shift()!;
      if (uri === cls.uri || ancestors.has(uri)) continue;
      ancestors.add(uri);
      const parents = uriToSuperclasses.get(uri);
      if (parents) queue.push(...parents);
    }
    result.set(cls.uri, ancestors);
  }
  return result;
});

export function isApplicable(
  classUri: string,
  domainClassUris: string[],
): boolean {
  if (domainClassUris.includes(classUri)) return true;
  const ancestors = classAncestors.value.get(classUri);
  if (!ancestors) return false;
  return domainClassUris.some((uri) => ancestors.has(uri));
}
