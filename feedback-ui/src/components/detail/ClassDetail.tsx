import { vocabulary, selectedVersion, currentProjectId } from "../../state/vocabulary";
import { navigate } from "../../router";
import { FeedbackSection } from "../feedback/FeedbackSection";
import type { VocabClass, VocabProperty } from "../../api/published";

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

function buildClassAncestors(
  classes: VocabClass[],
): Map<string, Set<string>> {
  const uriToSuperclasses = new Map<string, string[]>();
  for (const cls of classes) {
    uriToSuperclasses.set(cls.uri, cls.superclasses);
  }
  const result = new Map<string, Set<string>>();
  for (const cls of classes) {
    const ancestors = new Set<string>();
    const queue = [...cls.superclasses];
    while (queue.length > 0) {
      const uri = queue.shift()!;
      if (uri === cls.uri || ancestors.has(uri)) continue;
      ancestors.add(uri);
      const parents = uriToSuperclasses.get(uri);
      if (parents) queue.push(...parents);
    }
    result.set(cls.uri, ancestors);
  }
  return result;
}

interface InheritedGroup {
  ancestorUri: string;
  label: string;
  depth: number;
  properties: VocabProperty[];
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

  // Properties that use this class as range
  const rangeProperties = allProperties.filter(
    (p) => p.range_class === cls.uri
  );

  // Applicability closure: direct + inherited properties
  const ancestorMap = buildClassAncestors(allClasses);
  const classAncestors = ancestorMap.get(cls.uri) ?? new Set<string>();

  const applicableProperties = allProperties.filter((p) => {
    if (p.domain_class_uris.includes(cls.uri)) return true;
    return p.domain_class_uris.some((uri) => classAncestors.has(uri));
  });

  const directProperties = applicableProperties.filter((p) =>
    p.domain_class_uris.includes(cls.uri)
  );
  const directIds = new Set(directProperties.map((p) => p.id));

  // BFS for ancestor depths
  const ancestorDepth = new Map<string, number>();
  const depthQueue: [string, number][] = cls.superclasses.map(
    (uri) => [uri, 1] as [string, number]
  );
  const depthVisited = new Set<string>();
  while (depthQueue.length > 0) {
    const [uri, depth] = depthQueue.shift()!;
    if (depthVisited.has(uri)) continue;
    depthVisited.add(uri);
    ancestorDepth.set(uri, depth);
    const ancestorClass = allClasses.find((c) => c.uri === uri);
    if (ancestorClass) {
      for (const parentUri of ancestorClass.superclasses) {
        depthQueue.push([parentUri, depth + 1]);
      }
    }
  }

  // Group inherited properties by nearest ancestor (tie-break by label)
  const groupMap = new Map<string, InheritedGroup>();
  for (const prop of applicableProperties) {
    if (directIds.has(prop.id)) continue;
    let nearestUri: string | null = null;
    let nearestDepth = Infinity;
    let nearestLabel = "";
    for (const domainUri of prop.domain_class_uris) {
      const depth = ancestorDepth.get(domainUri);
      if (depth === undefined) continue;
      const label = allClasses.find((c) => c.uri === domainUri)?.label ?? extractLocalName(domainUri);
      if (depth < nearestDepth || (depth === nearestDepth && label.localeCompare(nearestLabel) < 0)) {
        nearestDepth = depth;
        nearestUri = domainUri;
        nearestLabel = label;
      }
    }
    if (nearestUri) {
      if (!groupMap.has(nearestUri)) {
        groupMap.set(nearestUri, {
          ancestorUri: nearestUri,
          label: nearestLabel,
          depth: nearestDepth,
          properties: [],
        });
      }
      groupMap.get(nearestUri)!.properties.push(prop);
    }
  }

  const inheritedGroups = [...groupMap.values()].sort((a, b) =>
    a.depth !== b.depth ? a.depth - b.depth : a.label.localeCompare(b.label)
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

      {(directProperties.length > 0 || inheritedGroups.length > 0) && (
        <div class="detail__section">
          <div class="detail__label">Properties</div>
          {directProperties.length > 0 && (
            <div>
              {inheritedGroups.length > 0 && (
                <div class="detail__text" style={{ fontWeight: 500, fontSize: "0.85em", color: "var(--color-text-secondary, #666)" }}>Direct</div>
              )}
              <div class="detail__link-list">
                {directProperties.map((p) => (
                  <span key={p.id}>
                    <PropertyLink id={p.id} label={p.label} />
                    {" "}({p.cardinality}{p.required ? ", required" : ""})
                  </span>
                ))}
              </div>
            </div>
          )}
          {inheritedGroups.map((group) => (
            <div key={group.ancestorUri}>
              <div class="detail__text" style={{ fontWeight: 500, fontSize: "0.85em", color: "var(--color-text-muted, #999)" }}>
                Inherited from <ClassLink uri={group.ancestorUri} />
              </div>
              <div class="detail__link-list">
                {group.properties.map((p) => (
                  <span key={p.id} style={{ opacity: 0.7 }}>
                    <PropertyLink id={p.id} label={p.label} />
                    {" "}({p.cardinality}{p.required ? ", required" : ""})
                  </span>
                ))}
              </div>
            </div>
          ))}
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
