import { signal } from "@preact/signals";
import type { ConceptScheme } from "../types/models";

export const schemes = signal<ConceptScheme[]>([]);
export const schemesLoading = signal(false);
export const schemesError = signal<string | null>(null);
export const currentScheme = signal<ConceptScheme | null>(null);
