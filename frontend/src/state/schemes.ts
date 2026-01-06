import { signal, computed } from "@preact/signals";
import type { ConceptScheme } from "../types/models";

export const schemes = signal<ConceptScheme[]>([]);
export const schemesLoading = signal(false);
export const schemesError = signal<string | null>(null);
export const currentScheme = signal<ConceptScheme | null>(null);

export const schemesById = computed(() => {
  const map = new Map<string, ConceptScheme>();
  for (const scheme of schemes.value) {
    map.set(scheme.id, scheme);
  }
  return map;
});
