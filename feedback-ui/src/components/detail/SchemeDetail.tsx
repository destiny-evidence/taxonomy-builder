import { vocabulary, selectedVersion } from "../../state/vocabulary";
import { navigate } from "../../router";
import { FeedbackSection } from "../feedback/FeedbackSection";
import type { VocabScheme } from "../../api/published";

interface SchemeDetailProps {
  schemeId: string;
}

function findScheme(schemeId: string): VocabScheme | null {
  const vocab = vocabulary.value;
  if (!vocab) return null;
  return vocab.schemes.find((s) => s.id === schemeId) ?? null;
}

export function SchemeDetail({ schemeId }: SchemeDetailProps) {
  const scheme = findScheme(schemeId);
  if (!scheme) return <div class="detail">Scheme not found</div>;

  const conceptCount = Object.keys(scheme.concepts).length;
  const topConcepts = scheme.top_concepts
    .map((id) => {
      const concept = scheme.concepts[id];
      return concept ? { id, label: concept.pref_label } : null;
    })
    .filter((c): c is { id: string; label: string } => c !== null);

  return (
    <div class="detail">
      <h1 class="detail__title">{scheme.title}</h1>
      <div class="detail__uri">{scheme.uri}</div>

      {scheme.description && (
        <div class="detail__section">
          <div class="detail__label">Description</div>
          <div class="detail__text">{scheme.description}</div>
        </div>
      )}

      <div class="detail__section">
        <div class="detail__label">Concepts</div>
        <div class="detail__text">{conceptCount} concept{conceptCount !== 1 ? "s" : ""}</div>
      </div>

      {topConcepts.length > 0 && (
        <div class="detail__section">
          <div class="detail__label">Top Concepts</div>
          <div class="detail__link-list">
            {topConcepts.map((c) => (
              <span
                key={c.id}
                class="detail__link"
                onClick={() => {
                  const version = selectedVersion.value;
                  if (version) navigate(version, "concept", c.id);
                }}
              >
                {c.label}
              </span>
            ))}
          </div>
        </div>
      )}

      <FeedbackSection
        entityType="scheme"
        entityId={schemeId}
        entityLabel={scheme.title}
      />
    </div>
  );
}
