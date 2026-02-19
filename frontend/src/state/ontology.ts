import { signal, computed } from "@preact/signals";
import type { CoreOntology, OntologyClass } from "../types/models";

export const ontology = signal<CoreOntology | null>(null);
export const ontologyLoading = signal(false);
export const ontologyError = signal<string | null>(null);
export const selectedClassUri = signal<string | null>(null);

export const ontologyClasses = computed<OntologyClass[]>(() =>
  ontology.value?.classes ?? []
);

export const selectedClass = computed<OntologyClass | null>(() => {
  if (!selectedClassUri.value || !ontology.value) return null;
  return ontologyClasses.value.find((c) => c.uri === selectedClassUri.value) ?? null;
});
