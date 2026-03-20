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

function extractLocalName(uri: string): string {
  const hashIndex = uri.lastIndexOf("#");
  const slashIndex = uri.lastIndexOf("/");
  const index = Math.max(hashIndex, slashIndex);
  return index >= 0 ? uri.substring(index + 1) : uri;
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

function ClassLink({ uri }: { uri: string }) {
  const version = selectedVersion.value;
  const projectId = currentProjectId.value;
  const allClasses = vocabulary.value?.classes ?? [];
  const target = allClasses.find((c) => c.uri === uri);
  if (!target) return <span>{extractLocalName(uri)}</span>;
  return (
    <span
      class="detail__link"
      onClick={() => version && projectId && navigate(projectId, version, "class", target.id)}
    >
      {target.label}
    </span>
  );
}

export function ClassDetail({ classId }: ClassDetailProps) {
  const cls = findClass(classId);
  if (!cls) return <div class="detail">Class not found</div>;

  const allProperties = vocabulary.value?.properties ?? [];
  const allClasses = vocabulary.value?.classes ?? [];

  // Properties that use this class as domain
  const domainProperties = allProperties.filter(
    (p) => p.domain_class_uris.includes(cls.uri)
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

      {(cls.superclasses.length > 0 || cls.subclasses.length > 0) && (
        <div class="detail__section">
          <div class="detail__label">Hierarchy</div>
          {cls.superclasses.length > 0 && (
            <div class="detail__text">
              Superclass:{" "}
              {cls.superclasses.map((uri, i) => (
                <span key={uri}>
                  {i > 0 && ", "}
                  <ClassLink uri={uri} />
                </span>
              ))}
            </div>
          )}
          {cls.subclasses.length > 0 && (
            <div class="detail__text">
              Subclasses:{" "}
              {cls.subclasses.map((uri, i) => (
                <span key={uri}>
                  {i > 0 && ", "}
                  <ClassLink uri={uri} />
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {cls.restrictions.length > 0 && (
        <div class="detail__section">
          <div class="detail__label">Restrictions</div>
          {cls.restrictions.map((r, i) => {
            const propLabel = allProperties.find(
              (p) => p.uri === r.on_property_uri
            )?.label ?? extractLocalName(r.on_property_uri);
            const valueLabel = allClasses.find(
              (c) => c.uri === r.value_uri
            )?.label ?? extractLocalName(r.value_uri);
            return (
              <div key={i} class="detail__text">
                <strong>{propLabel}</strong> {r.restriction_type} {valueLabel}
              </div>
            );
          })}
        </div>
      )}

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
