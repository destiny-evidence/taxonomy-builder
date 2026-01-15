import { useEffect } from "preact/hooks";
import { route } from "preact-router";
import { SchemesPane } from "../components/workspace/SchemesPane";
import { TreePane } from "../components/workspace/TreePane";
import { projects } from "../state/projects";
import { schemes, currentScheme } from "../state/schemes";
import { currentProject } from "../state/projects";
import {
  concepts,
  treeData,
  treeLoading,
  expandedPaths,
} from "../state/concepts";
import { projectsApi } from "../api/projects";
import { schemesApi } from "../api/schemes";
import { conceptsApi } from "../api/concepts";
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
      loadTree(schemeId);
      loadConcepts(schemeId);
    } else {
      currentScheme.value = null;
      treeData.value = [];
      concepts.value = [];
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

  async function loadTree(schemeId: string) {
    treeLoading.value = true;
    try {
      treeData.value = await conceptsApi.getTree(schemeId);
    } catch (err) {
      console.error("Failed to load tree:", err);
    } finally {
      treeLoading.value = false;
    }
  }

  async function loadConcepts(schemeId: string) {
    try {
      concepts.value = await conceptsApi.listForScheme(schemeId);
    } catch (err) {
      console.error("Failed to load concepts:", err);
    }
  }

  async function handleRefresh() {
    if (schemeId) {
      await Promise.all([loadTree(schemeId), loadConcepts(schemeId)]);
    }
  }

  function handleExpandAll() {
    const allPaths = new Set<string>();
    function collectPaths(nodes: typeof treeData.value, parentPath = "") {
      for (const node of nodes) {
        const path = parentPath ? `${parentPath}/${node.id}` : node.id;
        if (node.narrower.length > 0) {
          allPaths.add(path);
          collectPaths(node.narrower, path);
        }
      }
    }
    collectPaths(treeData.value);
    expandedPaths.value = allPaths;
  }

  function handleCollapseAll() {
    expandedPaths.value = new Set();
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
          <TreePane
            schemeId={schemeId}
            onExpandAll={handleExpandAll}
            onCollapseAll={handleCollapseAll}
            onRefresh={handleRefresh}
          />
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
