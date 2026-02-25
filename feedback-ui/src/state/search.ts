import { computed, signal } from "@preact/signals";
import { vocabulary } from "./vocabulary";
import { ownFeedback } from "./feedback";

export const searchQuery = signal("");

export interface SearchResult {
  type: "concept" | "scheme" | "class" | "property" | "feedback";
  id: string;
  label: string;
  /** For feedback results, the entity this feedback is about. */
  entityId?: string;
  entityType?: string;
  snippet?: string;
}

export const searchResults = computed<SearchResult[]>(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return [];

  const vocab = vocabulary.value;
  if (!vocab) return [];

  const results: SearchResult[] = [];

  // Search schemes
  for (const scheme of vocab.schemes) {
    if (scheme.title.toLowerCase().includes(q)) {
      results.push({ type: "scheme", id: scheme.id, label: scheme.title });
    }

    // Search concepts
    for (const [id, concept] of Object.entries(scheme.concepts)) {
      const matchLabel = concept.pref_label.toLowerCase().includes(q);
      const matchAlt = concept.alt_labels.some((a) =>
        a.toLowerCase().includes(q)
      );
      if (matchLabel || matchAlt) {
        results.push({ type: "concept", id, label: concept.pref_label });
      }
    }
  }

  // Search classes
  for (const cls of vocab.classes) {
    if (cls.label.toLowerCase().includes(q)) {
      results.push({ type: "class", id: cls.id, label: cls.label });
    }
  }

  // Search properties
  for (const prop of vocab.properties) {
    if (prop.label.toLowerCase().includes(q)) {
      results.push({ type: "property", id: prop.id, label: prop.label });
    }
  }

  // Search own feedback content
  for (const fb of ownFeedback.value) {
    if (fb.content.toLowerCase().includes(q)) {
      results.push({
        type: "feedback",
        id: fb.id,
        label: fb.entity_label,
        entityId: fb.entity_id,
        entityType: fb.entity_type,
        snippet: fb.content.slice(0, 100),
      });
    }
  }

  return results;
});
