import { vocabulary } from "../../state/vocabulary";
import type { VocabClass } from "../../api/published";

interface ClassDetailProps {
  classId: string;
}

function findClass(classId: string): VocabClass | null {
  const vocab = vocabulary.value;
  if (!vocab) return null;
  return vocab.classes.find((c) => c.id === classId) ?? null;
}

export function ClassDetail({ classId }: ClassDetailProps) {
  const cls = findClass(classId);
  if (!cls) return <div class="detail">Class not found</div>;

  // Find properties that use this class as domain
  const domainProperties = (vocabulary.value?.properties ?? []).filter(
    (p) => p.domain_class_uri === cls.uri
  );

  return (
    <div class="detail">
      <h1 class="detail__title">{cls.label}</h1>
      <div class="detail__uri">{cls.uri}</div>

      {cls.description && (
        <div class="detail__section">
          <div class="detail__label">Description</div>
          <div class="detail__text">{cls.description}</div>
        </div>
      )}

      {cls.scope_note && (
        <div class="detail__section">
          <div class="detail__label">Scope Note</div>
          <div class="detail__text">{cls.scope_note}</div>
        </div>
      )}

      <div class="detail__section">
        <div class="detail__label">Identifier</div>
        <div class="detail__text">{cls.identifier}</div>
      </div>

      {domainProperties.length > 0 && (
        <div class="detail__section">
          <div class="detail__label">Properties</div>
          <div class="detail__link-list">
            {domainProperties.map((p) => (
              <span key={p.id} class="detail__text">
                {p.label} ({p.cardinality}{p.required ? ", required" : ""})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
