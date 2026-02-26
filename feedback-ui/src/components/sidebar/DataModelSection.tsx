import { useSignal } from "@preact/signals";
import { navigate, route } from "../../router";
import { vocabulary, selectedVersion, currentProjectId } from "../../state/vocabulary";
import { isAuthenticated } from "../../state/auth";
import { feedbackCountForEntity } from "../../state/feedback";

export function DataModelSection() {
  const classesExpanded = useSignal(false);
  const propsExpanded = useSignal(false);
  const vocab = vocabulary.value;
  if (!vocab) return null;

  const classes = vocab.classes;
  const properties = vocab.properties;
  if (classes.length === 0 && properties.length === 0) return null;

  const classesAggCount = !classesExpanded.value && isAuthenticated.value
    ? classes.reduce((sum, cls) => sum + feedbackCountForEntity(cls.id, "class"), 0)
    : 0;

  const propsAggCount = !propsExpanded.value && isAuthenticated.value
    ? properties.reduce((sum, p) => sum + feedbackCountForEntity(p.id, "property"), 0)
    : 0;

  return (
    <div class="sidebar__group">
      <div class="sidebar__group-header">Data Model</div>
      <div class="sidebar__group-body">
        {classes.length > 0 && (
          <div class="sidebar__section">
            <div class="sidebar__section-header" role="button" tabIndex={0} aria-expanded={classesExpanded.value} onClick={() => (classesExpanded.value = !classesExpanded.value)} onKeyDown={(e: KeyboardEvent) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); classesExpanded.value = !classesExpanded.value; } }}>
              <svg class={`sidebar__chevron${classesExpanded.value ? " sidebar__chevron--open" : ""}`} width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span class="sidebar__section-title">Classes</span>
              {classesAggCount > 0 && <span class="sidebar__badge">{classesAggCount}</span>}
            </div>
            {classesExpanded.value && (
              <div class="sidebar__section-body">
                {classes.map((cls) => {
                  const count = isAuthenticated.value ? feedbackCountForEntity(cls.id, "class") : 0;
                  const version = selectedVersion.value;
                  const isActive = route.value.entityKind === "class" && route.value.entityId === cls.id;
                  const handleNav = () => {
                    if (isActive) { (document.querySelector(".detail__title") as HTMLElement)?.focus({ preventScroll: true }); return; }
                    const pid = currentProjectId.value; if (version && pid) navigate(pid, version, "class", cls.id);
                  };
                  return (
                    <div
                      key={cls.id}
                      class={`data-model-item${isActive ? " data-model-item--active" : ""}`}
                      role="button"
                      tabIndex={0}
                      onClick={handleNav}
                      onKeyDown={(e: KeyboardEvent) => { if (e.key === "Enter") handleNav(); }}
                    >
                      {cls.label}
                      {count > 0 && <span class="sidebar__badge">{count}</span>}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
        {properties.length > 0 && (
          <div class="sidebar__section">
            <div class="sidebar__section-header" role="button" tabIndex={0} aria-expanded={propsExpanded.value} onClick={() => (propsExpanded.value = !propsExpanded.value)} onKeyDown={(e: KeyboardEvent) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); propsExpanded.value = !propsExpanded.value; } }}>
              <svg class={`sidebar__chevron${propsExpanded.value ? " sidebar__chevron--open" : ""}`} width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span class="sidebar__section-title">Properties</span>
              {propsAggCount > 0 && <span class="sidebar__badge">{propsAggCount}</span>}
            </div>
            {propsExpanded.value && (
              <div class="sidebar__section-body">
                {properties.map((prop) => {
                  const count = isAuthenticated.value ? feedbackCountForEntity(prop.id, "property") : 0;
                  const version = selectedVersion.value;
                  const isActive = route.value.entityKind === "property" && route.value.entityId === prop.id;
                  const handleNav = () => {
                    if (isActive) { (document.querySelector(".detail__title") as HTMLElement)?.focus({ preventScroll: true }); return; }
                    const pid = currentProjectId.value; if (version && pid) navigate(pid, version, "property", prop.id);
                  };
                  return (
                    <div
                      key={prop.id}
                      class={`data-model-item${isActive ? " data-model-item--active" : ""}`}
                      role="button"
                      tabIndex={0}
                      onClick={handleNav}
                      onKeyDown={(e: KeyboardEvent) => { if (e.key === "Enter") handleNav(); }}
                    >
                      {prop.label}
                      {count > 0 && <span class="sidebar__badge">{count}</span>}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
