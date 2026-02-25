import type { Vocabulary } from "../src/api/published";

/**
 * Build a minimal Vocabulary for testing.
 * Override any top-level fields or nested structures via `overrides`.
 */
export function makeVocabulary(overrides: Partial<Vocabulary> = {}): Vocabulary {
  return {
    format_version: "1",
    version: "1.0",
    title: "Test",
    published_at: "2024-01-01",
    publisher: null,
    pre_release: false,
    previous_version_id: null,
    project: { id: "p1", name: "Test", description: null, namespace: null },
    schemes: [],
    classes: [],
    properties: [],
    ...overrides,
  };
}

/** Minimal concept with sensible defaults. */
export function makeConcept(overrides: Record<string, unknown> = {}) {
  return {
    pref_label: "Concept",
    identifier: "concept",
    uri: "http://example.org/concept",
    definition: null,
    scope_note: null,
    alt_labels: [] as string[],
    broader: [] as string[],
    related: [] as string[],
    ...overrides,
  };
}
