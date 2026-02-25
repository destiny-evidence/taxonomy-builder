import { useEffect } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { initRouter, destroyRouter, route } from "../../router";
import { loadProjects, projectName, selectedVersion } from "../../state/vocabulary";
import { AuthStatus } from "./AuthStatus";
import { Sidebar } from "../sidebar/Sidebar";
import { DetailPanel } from "../detail/DetailPanel";
import "./AppShell.css";

export function AppShell() {
  const mobileShowDetail = useSignal(false);

  useEffect(() => {
    initRouter();
    loadProjects();
    return destroyRouter;
  }, []);

  // On mobile, show detail panel when a route has an entity
  useEffect(() => {
    if (route.value.entityId) {
      mobileShowDetail.value = true;
    }
  }, [route.value.entityId]);

  function handleBack() {
    mobileShowDetail.value = false;
    window.location.hash = "";
  }

  const hasEntity = route.value.entityId !== null;
  const sidebarHidden = mobileShowDetail.value && hasEntity;
  const detailHidden = !hasEntity && !mobileShowDetail.value;

  return (
    <div class="app-shell">
      <header class="app-shell__header">
        <div class="app-shell__header-left">
          <span class="app-shell__title">{projectName.value || "Taxonomy Reader"}</span>
          {selectedVersion.value && (
            <span class="app-shell__version">v{selectedVersion.value}</span>
          )}
        </div>
        <AuthStatus />
      </header>
      <div class="app-shell__body">
        <div class={`app-shell__sidebar${sidebarHidden ? " app-shell__sidebar--hidden" : ""}`}>
          <Sidebar />
        </div>
        <div class={`app-shell__detail${detailHidden ? " app-shell__detail--hidden" : ""}`}>
          {hasEntity && (
            <button class="app-shell__back-btn" onClick={handleBack}>
              ← Back
            </button>
          )}
          <DetailPanel />
        </div>
      </div>
    </div>
  );
}
