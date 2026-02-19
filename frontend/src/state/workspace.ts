import { signal, computed } from "@preact/signals";

export type SelectionMode = "class" | "scheme" | null;

export const selectionMode = signal<SelectionMode>(null);

export const isClassMode = computed(() => selectionMode.value === "class");
export const isSchemeMode = computed(() => selectionMode.value === "scheme");
