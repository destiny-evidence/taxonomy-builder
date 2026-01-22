import Router from "preact-router";
import { useEffect } from "preact/hooks";
import { AppShell } from "./components/layout/AppShell";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { ProjectsPage } from "./pages/ProjectsPage";
import { SchemeWorkspacePage } from "./pages/SchemeWorkspacePage";
import { LoginPage } from "./pages/LoginPage";
import { initAuth } from "./api/auth";
import { authInitialized } from "./state/auth";

export function App() {
  useEffect(() => {
    initAuth();
  }, []);

  // Show nothing while initializing auth
  if (!authInitialized.value) {
    return null;
  }

  return (
    <AppShell>
      <Router>
        <LoginPage path="/login" />
        <ProtectedRoute path="/">
          <ProjectsPage />
        </ProtectedRoute>
        <ProtectedRoute path="/projects">
          <ProjectsPage />
        </ProtectedRoute>
        <ProtectedRoute path="/projects/:projectId">
          <SchemeWorkspacePage />
        </ProtectedRoute>
        <ProtectedRoute path="/projects/:projectId/schemes/:schemeId">
          <SchemeWorkspacePage />
        </ProtectedRoute>
      </Router>
    </AppShell>
  );
}
