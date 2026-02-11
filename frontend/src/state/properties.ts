import { signal } from "@preact/signals";
import type { Property, CoreOntologyResponse } from "../types/models";

export const properties = signal<Property[]>([]);
export const propertiesLoading = signal(false);
export const propertiesError = signal<string | null>(null);

export const coreOntology = signal<CoreOntologyResponse | null>(null);
export const coreOntologyLoading = signal(false);
