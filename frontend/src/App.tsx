import Router from "preact-router";
import { AppShell } from "./components/layout/AppShell";
import { ProjectsPage } from "./pages/ProjectsPage";
import { ProjectDetailPage } from "./pages/ProjectDetailPage";
import { SchemeDetailPage } from "./pages/SchemeDetailPage";

export function App() {
  return (
    <AppShell>
      <Router>
        <ProjectsPage path="/" />
        <ProjectDetailPage path="/projects/:projectId" />
        <SchemeDetailPage path="/schemes/:schemeId" />
      </Router>
    </AppShell>
  );
}
