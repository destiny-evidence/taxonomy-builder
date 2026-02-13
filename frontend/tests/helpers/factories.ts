import type { Concept } from "../../src/types/models";

export function makeConcept(overrides: Partial<Concept> & { id: string; pref_label: string }): Concept {
  return {
    scheme_id: "scheme-1",
    identifier: null,
    definition: null,
    scope_note: null,
    uri: null,
    alt_labels: [],
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    broader: [],
    related: [],
    ...overrides,
  };
}
