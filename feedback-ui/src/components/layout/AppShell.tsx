import { useEffect } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { initRouter, destroyRouter, route, navigateHome } from "../../router";
import { loadProjects, selectProject, projectName, selectedVersion, currentProjectId } from "../../state/vocabulary";
import { AuthStatus } from "./AuthStatus";
import { Sidebar } from "../sidebar/Sidebar";
import { DetailPanel } from "../detail/DetailPanel";
import { ProjectListPage } from "../projects/ProjectListPage";
import "./AppShell.css";

export function AppShell() {
  const mobileShowDetail = useSignal(false);

  useEffect(() => {
    initRouter();
    loadProjects();
    return destroyRouter;
  }, []);

  // When route's projectId changes, select that project
  const routedProjectId = route.value.projectId;
  useEffect(() => {
    if (routedProjectId && routedProjectId !== currentProjectId.value) {
      selectProject(routedProjectId);
    }
  }, [routedProjectId]);

  // On mobile, show detail panel when a route has an entity
  useEffect(() => {
    if (route.value.entityId) {
      mobileShowDetail.value = true;
    }
  }, [route.value.entityId]);

  function handleBack() {
    mobileShowDetail.value = false;
    navigateHome();
  }

  const isProjectView = route.value.projectId !== null;
  const hasEntity = route.value.entityId !== null;
  const sidebarHidden = mobileShowDetail.value && hasEntity;
  const detailHidden = !hasEntity && !mobileShowDetail.value;

  return (
    <div class="app-shell">
      <header class="app-shell__header">
        <div class="app-shell__header-left">
          {isProjectView ? (
            <>
              <span class="app-shell__breadcrumb-link" onClick={navigateHome}>
                Vocabularies
              </span>
              <span class="app-shell__breadcrumb-sep" aria-hidden="true">›</span>
              <span class="app-shell__title">
                {projectName.value || "Taxonomy Reader"}
              </span>
              {selectedVersion.value && (
                <span class="app-shell__version">v{selectedVersion.value}</span>
              )}
            </>
          ) : (
            <span class="app-shell__title">Taxonomy Reader</span>
          )}
        </div>
        <AuthStatus />
      </header>
      {isProjectView ? (
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
      ) : (
        <ProjectListPage />
      )}
    </div>
  );
}
