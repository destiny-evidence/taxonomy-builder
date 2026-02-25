import { useSignal } from "@preact/signals";
import { navigate, route } from "../../router";
import { vocabulary, selectedVersion } from "../../state/vocabulary";

export function DataModelSection() {
  const expanded = useSignal(true);
  const vocab = vocabulary.value;
  if (!vocab) return null;

  const classes = vocab.classes;
  const properties = vocab.properties;
  if (classes.length === 0 && properties.length === 0) return null;

  return (
    <div class="sidebar__section">
      <div class="sidebar__section-header" onClick={() => (expanded.value = !expanded.value)}>
        <span class="sidebar__section-title">Data Model</span>
        <span class={`sidebar__toggle${expanded.value ? " sidebar__toggle--open" : ""}`}>
          ▸
        </span>
      </div>
      {expanded.value && (
        <div>
          {classes.length > 0 && (
            <div>
              <div class="sidebar__section-title" style="font-size: var(--font-size-xs); margin: var(--spacing-sm) 0 var(--spacing-xs)">
                Classes
              </div>
              {classes.map((cls) => (
                <div
                  key={cls.id}
                  class={`data-model-item${route.value.entityKind === "class" && route.value.entityId === cls.id ? " data-model-item--active" : ""}`}
                  onClick={() => {
                    const version = selectedVersion.value;
                    if (version) navigate(version, "class", cls.id);
                  }}
                >
                  {cls.label}
                </div>
              ))}
            </div>
          )}
          {properties.length > 0 && (
            <div>
              <div class="sidebar__section-title" style="font-size: var(--font-size-xs); margin: var(--spacing-sm) 0 var(--spacing-xs)">
                Properties
              </div>
              {properties.map((prop) => (
                <div
                  key={prop.id}
                  class={`data-model-item${route.value.entityKind === "property" && route.value.entityId === prop.id ? " data-model-item--active" : ""}`}
                  onClick={() => {
                    const version = selectedVersion.value;
                    if (version) navigate(version, "property", prop.id);
                  }}
                >
                  {prop.label}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
