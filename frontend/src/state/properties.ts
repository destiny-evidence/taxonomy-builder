import { signal, computed } from "@preact/signals";
import type { Property } from "../types/models";

export const properties = signal<Property[]>([]);
export const propertiesLoading = signal(false);
export const propertiesError = signal<string | null>(null);
export const selectedPropertyId = signal<string | null>(null);

export interface CreatingPropertyConfig {
  projectId: string;
  domainClassUri?: string;
}

export const creatingProperty = signal<CreatingPropertyConfig | null>(null);

export const selectedProperty = computed(() => {
  if (!selectedPropertyId.value) return null;
  return properties.value.find((p) => p.id === selectedPropertyId.value) ?? null;
});
