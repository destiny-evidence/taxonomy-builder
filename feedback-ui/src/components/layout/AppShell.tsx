import { useEffect } from "preact/hooks";
import { initRouter, destroyRouter, route, navigateHome, navigateToProject, goBack, mobileView } from "../../router";
import { loadProjects, selectProject, resolveLatestVersion, projectName, selectedVersion, currentProjectId } from "../../state/vocabulary";
import { AuthStatus } from "./AuthStatus";
import { isOffline } from "../../state/network";
import { Sidebar } from "../sidebar/Sidebar";
import { DetailPanel } from "../detail/DetailPanel";
import { ProjectListPage } from "../projects/ProjectListPage";
import "./AppShell.css";

export function AppShell() {
  useEffect(() => {
    initRouter();
    loadProjects();
    return destroyRouter;
  }, []);

  // When route's project/version changes, select that project
  const routedProjectId = route.value.projectId;
  const routedVersion = route.value.version;
  useEffect(() => {
    if (!routedProjectId) return;
    if (routedVersion) {
      if (routedProjectId !== currentProjectId.value) {
        selectProject(routedProjectId, routedVersion);
      }
    } else {
      // Versionless route — resolve best version from project index
      resolveLatestVersion(routedProjectId).then((version) => {
        if (version) navigateToProject(routedProjectId, version, { replace: true });
        else navigateHome();
      });
    }
  }, [routedProjectId, routedVersion]);

  function handleBack() {
    if (!goBack()) {
      mobileView.value = "sidebar";
      const pid = route.value.projectId;
      const ver = route.value.version;
      if (pid && ver) navigateToProject(pid, ver);
      else navigateHome();
    }
  }

  function handleProjectNameClick() {
    const pid = route.value.projectId;
    const ver = route.value.version;
    if (pid && ver) {
      navigateToProject(pid, ver);
      mobileView.value = "detail";
    }
  }

  const isProjectView = route.value.projectId !== null;
  const isMobileDetail = mobileView.value === "detail";

  return (
    <div class="app-shell">
      <header class="app-shell__header">
        <div class="app-shell__header-left">
          {isProjectView ? (
            <>
              <span class="app-shell__breadcrumb-link" role="link" tabIndex={0} onClick={navigateHome} onKeyDown={(e: KeyboardEvent) => { if (e.key === "Enter") navigateHome(); }}>
                Vocabularies
              </span>
              <svg class="app-shell__breadcrumb-sep" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span
                class="app-shell__title app-shell__title--link"
                role="link"
                tabIndex={0}
                onClick={handleProjectNameClick}
                onKeyDown={(e: KeyboardEvent) => { if (e.key === "Enter") handleProjectNameClick(); }}
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
        {isOffline.value && (
          <span class="app-shell__offline">Offline</span>
        )}
        <AuthStatus />
      </header>
      {isProjectView ? (
        <div class="app-shell__body">
          <div class={`app-shell__sidebar${isMobileDetail ? " app-shell__sidebar--hidden" : ""}`}>
            <Sidebar />
          </div>
          <div class={`app-shell__detail${isMobileDetail ? "" : " app-shell__detail--hidden"}`}>
            {isMobileDetail && (
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
