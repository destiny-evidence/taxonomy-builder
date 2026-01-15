import { useEffect } from "preact/hooks";
import { route } from "preact-router";
import { SchemesPane } from "../components/workspace/SchemesPane";
import { projects } from "../state/projects";
import { schemes, currentScheme } from "../state/schemes";
import { currentProject } from "../state/projects";
import { projectsApi } from "../api/projects";
import { schemesApi } from "../api/schemes";
import "./SchemeWorkspacePage.css";

interface SchemeWorkspacePageProps {
  path?: string;
  projectId?: string;
  schemeId?: string;
}

export function SchemeWorkspacePage({
  projectId,
  schemeId,
}: SchemeWorkspacePageProps) {
  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
      loadSchemes(projectId);
    }
  }, [projectId]);

  useEffect(() => {
    if (schemeId) {
      loadScheme(schemeId);
    } else {
      currentScheme.value = null;
    }
  }, [schemeId]);

  async function loadProject(id: string) {
    try {
      const project = await projectsApi.get(id);
      currentProject.value = project;
      // Also load all projects for the dropdown
      if (projects.value.length === 0) {
        projects.value = await projectsApi.list();
      }
    } catch (err) {
      console.error("Failed to load project:", err);
    }
  }

  async function loadSchemes(projectId: string) {
    try {
      schemes.value = await schemesApi.listForProject(projectId);
    } catch (err) {
      console.error("Failed to load schemes:", err);
    }
  }

  async function loadScheme(id: string) {
    try {
      currentScheme.value = await schemesApi.get(id);
    } catch (err) {
      console.error("Failed to load scheme:", err);
    }
  }

  function handleSchemeSelect(schemeId: string) {
    route(`/projects/${projectId}/schemes/${schemeId}`);
  }

  function handleProjectChange(newProjectId: string) {
    route(`/projects/${newProjectId}`);
  }

  if (!projectId) {
    return <div>Project ID required</div>;
  }

  return (
    <div class="scheme-workspace">
      <SchemesPane
        projectId={projectId}
        currentSchemeId={schemeId ?? null}
        onSchemeSelect={handleSchemeSelect}
        onProjectChange={handleProjectChange}
      />

      <div class="scheme-workspace__main">
        {schemeId ? (
          <div class="scheme-workspace__placeholder">
            Tree pane for scheme {schemeId}
          </div>
        ) : (
          <div class="scheme-workspace__placeholder">
            Select a scheme from the list
          </div>
        )}
      </div>

      <div class="scheme-workspace__detail">
        <div class="scheme-workspace__placeholder">Concept details pane</div>
      </div>
    </div>
  );
}
