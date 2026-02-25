import {
  vocabulary,
  projectIndex,
  projectIndexLoading,
  selectedVersion,
  switchVersion,
} from "../../state/vocabulary";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function VersionList() {
  const index = projectIndex.value;
  const versions = index?.versions ?? [];
  const current = selectedVersion.value;
  const latest = index?.latest_version;

  if (projectIndexLoading.value) {
    return <div class="about__versions-loading">Loading versions…</div>;
  }

  if (versions.length === 0) return null;

  return (
    <div class="detail__section">
      <div class="detail__label">Versions</div>
      <div class="about__version-list">
        {versions.map((entry) => {
          const isCurrent = entry.version === current;
          const isLatest = entry.version === latest;
          return (
            <div
              key={entry.version}
              class={`about__version-card${isCurrent ? " about__version-card--current" : ""}`}
              onClick={() => !isCurrent && switchVersion(entry.version)}
              role={isCurrent ? undefined : "button"}
            >
              <div class="about__version-header">
                <span class="about__version-number">
                  v{entry.version}
                  {isLatest && (
                    <span class="about__latest-badge">latest</span>
                  )}
                  {entry.pre_release && (
                    <span class="about__pre-release">pre-release</span>
                  )}
                  {isCurrent && (
                    <span class="about__current-badge">current</span>
                  )}
                </span>
              </div>
              {entry.title && (
                <div class="about__version-title">{entry.title}</div>
              )}
              <div class="about__version-meta">
                {formatDate(entry.published_at)}
                {entry.publisher && <> · {entry.publisher}</>}
                {entry.content_summary && (
                  <>
                    {" · "}
                    {entry.content_summary.concepts} concepts,{" "}
                    {entry.content_summary.schemes} schemes,{" "}
                    {entry.content_summary.classes} classes,{" "}
                    {entry.content_summary.properties} properties
                  </>
                )}
              </div>
              {entry.notes && (
                <div class="about__version-notes">{entry.notes}</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function WelcomePanel() {
  const vocab = vocabulary.value;
  if (!vocab) {
    return (
      <div class="welcome">
        <div class="welcome__title">Select an entity to view details</div>
        <div class="welcome__subtitle">
          Browse concept schemes and data model in the sidebar
        </div>
      </div>
    );
  }

  const { project } = vocab;
  const totalConcepts = vocab.schemes.reduce(
    (sum, s) => sum + Object.keys(s.concepts).length,
    0
  );

  return (
    <div class="detail">
      <h1 class="detail__title">{project.name}</h1>

      {project.description && (
        <div class="detail__section">
          <div class="detail__text">{project.description}</div>
        </div>
      )}

      {project.namespace && (
        <div class="detail__section">
          <div class="detail__label">Namespace</div>
          <div class="detail__uri">{project.namespace}</div>
        </div>
      )}

      <div class="detail__section">
        <div class="detail__label">Contents</div>
        <div class="about__summary">
          <div class="about__summary-item">
            <span class="about__summary-count">{vocab.schemes.length}</span>
            concept scheme{vocab.schemes.length !== 1 ? "s" : ""}
          </div>
          <div class="about__summary-item">
            <span class="about__summary-count">{totalConcepts}</span>
            concept{totalConcepts !== 1 ? "s" : ""}
          </div>
          <div class="about__summary-item">
            <span class="about__summary-count">{vocab.classes.length}</span>
            class{vocab.classes.length !== 1 ? "es" : ""}
          </div>
          <div class="about__summary-item">
            <span class="about__summary-count">{vocab.properties.length}</span>
            propert{vocab.properties.length !== 1 ? "ies" : "y"}
          </div>
        </div>
      </div>

      <VersionList />
    </div>
  );
}
