import { useEffect, useState } from "preact/hooks";
import { route } from "preact-router";
import { SchemesPane } from "../components/workspace/SchemesPane";
import { TreePane } from "../components/workspace/TreePane";
import { ConceptPane } from "../components/workspace/ConceptPane";
import { ConceptForm } from "../components/concepts/ConceptForm";
import { ExportModal } from "../components/schemes/ExportModal";
import { HistoryPanel } from "../components/history/HistoryPanel";
import { VersionsPanel } from "../components/versions/VersionsPanel";
import { Modal } from "../components/common/Modal";
import { projects } from "../state/projects";
import { schemes, currentScheme } from "../state/schemes";
import { currentProject } from "../state/projects";
import {
  concepts,
  treeData,
  treeLoading,
  expandedPaths,
  selectedConceptId,
  selectedConcept,
} from "../state/concepts";
import { projectsApi } from "../api/projects";
import { schemesApi } from "../api/schemes";
import { conceptsApi } from "../api/concepts";
import type { Concept } from "../types/models";
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
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isVersionsOpen, setIsVersionsOpen] = useState(false);
  const [editingConcept, setEditingConcept] = useState<Concept | null>(null);
  const [initialBroaderId, setInitialBroaderId] = useState<string | null>(null);
  const [formKey, setFormKey] = useState(0);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

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
    // Clear selection when changing schemes
    selectedConceptId.value = null;
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

  function handleEdit() {
    if (selectedConcept.value) {
      setEditingConcept(selectedConcept.value);
      setIsFormOpen(true);
    }
  }

  async function handleDelete() {
    if (selectedConcept.value && schemeId) {
      try {
        await conceptsApi.delete(selectedConcept.value.id);
        selectedConceptId.value = null;
        await handleRefresh();
      } catch (err) {
        console.error("Failed to delete concept:", err);
      }
    }
  }

  function handleFormClose() {
    setIsFormOpen(false);
    setEditingConcept(null);
  }

  async function handleFormSuccess() {
    handleFormClose();
    if (schemeId) {
      await handleRefresh();
      // Refresh selected concept if it was edited
      if (selectedConceptId.value) {
        const updated = await conceptsApi.get(selectedConceptId.value);
        concepts.value = concepts.value.map((c) =>
          c.id === updated.id ? updated : c
        );
      }
    }
  }

  function handleCreate() {
    setEditingConcept(null);
    setInitialBroaderId(null);
    setFormKey((k) => k + 1);
    setIsFormOpen(true);
  }

  function handleAddChild(parentId: string) {
    setEditingConcept(null);
    setInitialBroaderId(parentId);
    setFormKey((k) => k + 1);
    setIsFormOpen(true);
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
            onCreate={handleCreate}
            onAddChild={handleAddChild}
            onExport={() => setIsExportOpen(true)}
            onHistory={() => {
              setHistoryRefreshKey((k) => k + 1);
              setIsHistoryOpen(true);
            }}
            onVersions={() => setIsVersionsOpen(true)}
          />
        ) : (
          <div class="scheme-workspace__placeholder">
            Select a scheme from the list
          </div>
        )}
      </div>

      <div class="scheme-workspace__detail">
        {schemeId ? (
          <ConceptPane
            onEdit={handleEdit}
            onDelete={handleDelete}
            onRefresh={handleRefresh}
          />
        ) : (
          <div class="scheme-workspace__placeholder">
            Select a scheme to view concepts
          </div>
        )}
      </div>

      <Modal
        isOpen={isFormOpen}
        title={editingConcept ? "Edit Concept" : "New Concept"}
        onClose={handleFormClose}
      >
        <ConceptForm
          key={editingConcept?.id ?? formKey}
          schemeId={schemeId!}
          schemeUri={currentScheme.value?.uri}
          concept={editingConcept}
          initialBroaderId={initialBroaderId}
          onSuccess={handleFormSuccess}
          onCancel={handleFormClose}
        />
      </Modal>

      <ExportModal
        isOpen={isExportOpen}
        schemeId={schemeId!}
        schemeTitle={currentScheme.value?.title ?? ""}
        onClose={() => setIsExportOpen(false)}
      />

      <Modal
        isOpen={isHistoryOpen}
        title="History"
        onClose={() => setIsHistoryOpen(false)}
      >
        <HistoryPanel schemeId={schemeId!} refreshKey={historyRefreshKey} />
      </Modal>

      <Modal
        isOpen={isVersionsOpen}
        title="Versions"
        onClose={() => setIsVersionsOpen(false)}
      >
        <VersionsPanel schemeId={schemeId!} />
      </Modal>
    </div>
  );
}
