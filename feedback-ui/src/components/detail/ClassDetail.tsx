import { vocabulary, selectedVersion, currentProjectId } from "../../state/vocabulary";
import { navigate } from "../../router";
import { FeedbackSection } from "../feedback/FeedbackSection";
import type { VocabClass } from "../../api/published";

interface ClassDetailProps {
  classId: string;
}

function findClass(classId: string): VocabClass | null {
  const vocab = vocabulary.value;
  if (!vocab) return null;
  return vocab.classes.find((c) => c.id === classId) ?? null;
}

function PropertyLink({ id, label }: { id: string; label: string }) {
  const version = selectedVersion.value;
  const projectId = currentProjectId.value;
  return (
    <span
      class="detail__link"
      onClick={() => version && projectId && navigate(projectId, version, "property", id)}
    >
      {label}
    </span>
  );
}

export function ClassDetail({ classId }: ClassDetailProps) {
  const cls = findClass(classId);
  if (!cls) return <div class="detail">Class not found</div>;

  const allProperties = vocabulary.value?.properties ?? [];

  // Properties that use this class as domain
  const domainProperties = allProperties.filter(
    (p) => p.domain_class_uri === cls.uri
  );

  // Properties that use this class as range
  const rangeProperties = allProperties.filter(
    (p) => p.range_class === cls.uri
  );

  return (
    <div class="detail">
      <h1 class="detail__title" tabIndex={0}>{cls.label}</h1>
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
              <span key={p.id}>
                <PropertyLink id={p.id} label={p.label} />
                {" "}({p.cardinality}{p.required ? ", required" : ""})
              </span>
            ))}
          </div>
        </div>
      )}

      {rangeProperties.length > 0 && (
        <div class="detail__section">
          <div class="detail__label">Range of</div>
          <div class="detail__link-list">
            {rangeProperties.map((p) => (
              <PropertyLink key={p.id} id={p.id} label={p.label} />
            ))}
          </div>
        </div>
      )}

      <FeedbackSection
        entityType="class"
        entityId={classId}
        entityLabel={cls.label}
      />
    </div>
  );
}
