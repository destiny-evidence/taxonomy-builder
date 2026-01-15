import Router from "preact-router";
import { AppShell } from "./components/layout/AppShell";
import { ProjectsPage } from "./pages/ProjectsPage";
import { SchemeDetailPage } from "./pages/SchemeDetailPage";
import { SchemeWorkspacePage } from "./pages/SchemeWorkspacePage";

export function App() {
  return (
    <AppShell>
      <Router>
        <ProjectsPage path="/" />
        <SchemeWorkspacePage path="/projects/:projectId" />
        <SchemeWorkspacePage path="/projects/:projectId/schemes/:schemeId" />
        <SchemeDetailPage path="/schemes/:schemeId" />
      </Router>
    </AppShell>
  );
}
