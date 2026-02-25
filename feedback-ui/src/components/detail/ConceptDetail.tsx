import { vocabulary, selectedVersion } from "../../state/vocabulary";
import { navigate } from "../../router";
import { FeedbackSection } from "../feedback/FeedbackSection";
import type { VocabConcept } from "../../api/published";

interface ConceptDetailProps {
  conceptId: string;
}

/** Find a concept across all schemes, returning the concept and its scheme id. */
function findConcept(
  conceptId: string
): { concept: VocabConcept; schemeId: string } | null {
  const vocab = vocabulary.value;
  if (!vocab) return null;
  for (const scheme of vocab.schemes) {
    const concept = scheme.concepts[conceptId];
    if (concept) return { concept, schemeId: scheme.id };
  }
  return null;
}

function ConceptLink({ id, label }: { id: string; label: string }) {
  const version = selectedVersion.value;
  return (
    <span
      class="detail__link"
      onClick={() => version && navigate(version, "concept", id)}
    >
      {label}
    </span>
  );
}

function resolveLabel(id: string): string {
  const found = findConcept(id);
  return found?.concept.pref_label ?? id;
}

export function ConceptDetail({ conceptId }: ConceptDetailProps) {
  // Read vocabulary.value directly to ensure signal subscription
  const vocab = vocabulary.value;
  if (!vocab) return <div class="detail">Loading...</div>;

  let result: { concept: VocabConcept; schemeId: string } | null = null;
  for (const scheme of vocab.schemes) {
    const concept = scheme.concepts[conceptId];
    if (concept) {
      result = { concept, schemeId: scheme.id };
      break;
    }
  }
  if (!result) return <div class="detail">Concept not found</div>;

  const { concept } = result;

  return (
    <div class="detail">
      <h1 class="detail__title">{concept.pref_label}</h1>
      <div class="detail__uri">{concept.uri}</div>

      {concept.definition && (
        <div class="detail__section">
          <div class="detail__label">Definition</div>
          <div class="detail__text">{concept.definition}</div>
        </div>
      )}

      {concept.scope_note && (
        <div class="detail__section">
          <div class="detail__label">Scope Note</div>
          <div class="detail__text">{concept.scope_note}</div>
        </div>
      )}

      {concept.alt_labels.length > 0 && (
        <div class="detail__section">
          <div class="detail__label">Alternative Labels</div>
          <div class="detail__tag-list">
            {concept.alt_labels.map((label) => (
              <span key={label} class="detail__tag">{label}</span>
            ))}
          </div>
        </div>
      )}

      {concept.broader.length > 0 && (
        <div class="detail__section">
          <div class="detail__label">Broader</div>
          <div class="detail__link-list">
            {concept.broader.map((id) => (
              <ConceptLink key={id} id={id} label={resolveLabel(id)} />
            ))}
          </div>
        </div>
      )}

      {concept.related.length > 0 && (
        <div class="detail__section">
          <div class="detail__label">Related</div>
          <div class="detail__link-list">
            {concept.related.map((id) => (
              <ConceptLink key={id} id={id} label={resolveLabel(id)} />
            ))}
          </div>
        </div>
      )}

      <FeedbackSection
        entityType="concept"
        entityId={conceptId}
        entityLabel={concept.pref_label}
      />
    </div>
  );
}
