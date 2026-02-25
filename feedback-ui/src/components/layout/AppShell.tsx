import { useEffect } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { initRouter, destroyRouter, route, navigateHome, navigateToProject } from "../../router";
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

  // When route's project/version changes, select that project
  const routedProjectId = route.value.projectId;
  const routedVersion = route.value.version;
  useEffect(() => {
    if (routedProjectId && routedVersion && routedProjectId !== currentProjectId.value) {
      selectProject(routedProjectId, routedVersion);
    }
  }, [routedProjectId, routedVersion]);

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
              <svg class="app-shell__breadcrumb-sep" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span
                class="app-shell__title app-shell__title--link"
                onClick={() => {
                  const pid = route.value.projectId;
                  const ver = route.value.version;
                  if (pid && ver) navigateToProject(pid, ver);
                }}
              >
                {projectName.value || "Taxonomy Reader"}
                {selectedVersion.value && (
                  <span class="app-shell__version">v{selectedVersion.value}</span>
                )}
              </span>
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
