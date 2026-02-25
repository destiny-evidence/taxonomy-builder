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

  return (
    <div class="sidebar__group">
      <div class="sidebar__group-header">Data Model</div>
      <div class="sidebar__group-body">
        {classes.length > 0 && (
          <div class="sidebar__section">
            <div class="sidebar__section-header" onClick={() => (classesExpanded.value = !classesExpanded.value)}>
              <svg class={`sidebar__chevron${classesExpanded.value ? " sidebar__chevron--open" : ""}`} width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span class="sidebar__section-title">Classes</span>
            </div>
            {classesExpanded.value && (
              <div class="sidebar__section-body">
                {classes.map((cls) => {
                  const version = selectedVersion.value ?? "";
                  const count = isAuthenticated.value ? feedbackCountForEntity(cls.id, version, "class") : 0;
                  return (
                    <div
                      key={cls.id}
                      class={`data-model-item${route.value.entityKind === "class" && route.value.entityId === cls.id ? " data-model-item--active" : ""}`}
                      onClick={() => { const pid = currentProjectId.value; if (version && pid) navigate(pid, version, "class", cls.id); }}
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
            <div class="sidebar__section-header" onClick={() => (propsExpanded.value = !propsExpanded.value)}>
              <svg class={`sidebar__chevron${propsExpanded.value ? " sidebar__chevron--open" : ""}`} width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span class="sidebar__section-title">Properties</span>
            </div>
            {propsExpanded.value && (
              <div class="sidebar__section-body">
                {properties.map((prop) => {
                  const version = selectedVersion.value ?? "";
                  const count = isAuthenticated.value ? feedbackCountForEntity(prop.id, version, "property") : 0;
                  return (
                    <div
                      key={prop.id}
                      class={`data-model-item${route.value.entityKind === "property" && route.value.entityId === prop.id ? " data-model-item--active" : ""}`}
                      onClick={() => { const pid = currentProjectId.value; if (version && pid) navigate(pid, version, "property", prop.id); }}
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
