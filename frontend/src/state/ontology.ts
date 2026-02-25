import { signal, computed } from "@preact/signals";
import type { OntologyClass } from "../types/models";

export const ontologyClasses = signal<OntologyClass[]>([]);
export const selectedClassUri = signal<string | null>(null);

export const selectedClass = computed<OntologyClass | null>(() => {
  if (!selectedClassUri.value) return null;
  return ontologyClasses.value.find((c) => c.uri === selectedClassUri.value) ?? null;
});
