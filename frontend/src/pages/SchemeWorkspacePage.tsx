import { useEffect, useState } from "preact/hooks";
import { route } from "preact-router";
import { ProjectPane } from "../components/workspace/ProjectPane";
import { TreePane } from "../components/workspace/TreePane";
import { ConceptPane } from "../components/workspace/ConceptPane";
import { ClassDetailPane } from "../components/workspace/ClassDetailPane";
import { PropertyPane } from "../components/workspace/PropertyPane";
import { ConceptForm } from "../components/concepts/ConceptForm";
import { PropertyForm } from "../components/properties/PropertyForm";
import { SchemeForm } from "../components/schemes/SchemeForm";
import { ExportModal } from "../components/schemes/ExportModal";
import { ImportModal } from "../components/schemes/ImportModal";
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
import { selectionMode, isClassMode, isSchemeMode } from "../state/workspace";
import { selectedClassUri, selectedClass, ontology } from "../state/ontology";
import { properties, selectedPropertyId } from "../state/properties";
import { projectsApi } from "../api/projects";
import { schemesApi } from "../api/schemes";
import { conceptsApi } from "../api/concepts";
import { ontologyApi } from "../api/ontology";
import { propertiesApi } from "../api/properties";
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
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [isSchemeFormOpen, setIsSchemeFormOpen] = useState(false);
  const [isPropertyFormOpen, setIsPropertyFormOpen] = useState(false);
  const [editingConcept, setEditingConcept] = useState<Concept | null>(null);
  const [initialBroaderId, setInitialBroaderId] = useState<string | null>(null);
  const [formKey, setFormKey] = useState(0);

  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
      loadSchemes(projectId);
      loadOntology();
      loadProperties(projectId);
    }
  }, [projectId]);

  useEffect(() => {
    if (schemeId) {
      // When navigating to a scheme, set scheme mode
      selectionMode.value = "scheme";
      selectedClassUri.value = null;
      selectedPropertyId.value = null;
      loadScheme(schemeId);
      loadTree(schemeId);
      loadConcepts(schemeId);
    } else {
      currentScheme.value = null;
      treeData.value = [];
      concepts.value = [];
    }
    // Clear concept selection when changing schemes
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

  async function loadOntology() {
    try {
      ontology.value = await ontologyApi.get();
    } catch (err) {
      console.error("Failed to load ontology:", err);
    }
  }

  async function loadProperties(projectId: string) {
    try {
      properties.value = await propertiesApi.listForProject(projectId);
    } catch (err) {
      console.error("Failed to load properties:", err);
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

  async function handlePropertiesRefresh() {
    if (projectId) {
      await loadProperties(projectId);
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

  function handleClassSelect(classUri: string) {
    selectionMode.value = "class";
    selectedClassUri.value = classUri;
    selectedPropertyId.value = null;
    selectedConceptId.value = null;
    // Clear scheme from URL when selecting a class
    route(`/projects/${projectId}`);
  }

  function handleSchemeSelect(schemeId: string) {
    selectionMode.value = "scheme";
    selectedClassUri.value = null;
    selectedPropertyId.value = null;
    selectedConceptId.value = null;
    route(`/projects/${projectId}/schemes/${schemeId}`);
  }

  function handleSchemeNavigate(schemeId: string) {
    handleSchemeSelect(schemeId);
  }

  function handlePropertySelect(propertyId: string) {
    selectedPropertyId.value = propertyId;
  }

  async function handleConceptDelete() {
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

  async function handlePropertyDelete() {
    // PropertyDetail handles deletion internally
    await handlePropertiesRefresh();
  }

  function handleFormClose() {
    setIsFormOpen(false);
    setEditingConcept(null);
  }

  async function handleFormSuccess() {
    handleFormClose();
    if (schemeId) {
      await handleRefresh();
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

  function handleNewProperty() {
    setIsPropertyFormOpen(true);
  }

  async function handlePropertyFormSuccess() {
    setIsPropertyFormOpen(false);
    await handlePropertiesRefresh();
  }

  async function handleImportSuccess() {
    if (projectId) {
      await loadSchemes(projectId);
    }
  }

  async function handleSchemeFormSuccess() {
    setIsSchemeFormOpen(false);
    if (projectId) {
      await loadSchemes(projectId);
    }
  }

  if (!projectId) {
    return <div>Project ID required</div>;
  }

  return (
    <div class="scheme-workspace">
      {/* Pane 1: Project navigation */}
      <ProjectPane
        projectId={projectId}
        currentSchemeId={schemeId ?? null}
        onSchemeSelect={handleSchemeSelect}
        onClassSelect={handleClassSelect}
        onNewScheme={() => setIsSchemeFormOpen(true)}
        onImport={() => setIsImportOpen(true)}
      />

      {/* Pane 2: Context-dependent detail */}
      <div class="scheme-workspace__main">
        {isClassMode.value && selectedClass.value ? (
          <ClassDetailPane
            classUri={selectedClassUri.value!}
            projectId={projectId}
            onPropertySelect={handlePropertySelect}
            onNewProperty={handleNewProperty}
            onSchemeNavigate={handleSchemeNavigate}
          />
        ) : isSchemeMode.value && schemeId ? (
          <TreePane
            schemeId={schemeId}
            onExpandAll={handleExpandAll}
            onCollapseAll={handleCollapseAll}
            onRefresh={handleRefresh}
            onCreate={handleCreate}
            onAddChild={handleAddChild}
            onExport={() => setIsExportOpen(true)}
          />
        ) : (
          <div class="scheme-workspace__placeholder">
            Select a class or scheme from the list
          </div>
        )}
      </div>

      {/* Pane 3: Context-dependent item detail */}
      <div class="scheme-workspace__detail">
        {isClassMode.value ? (
          <PropertyPane
            onDelete={handlePropertyDelete}
            onRefresh={handlePropertiesRefresh}
            onSchemeNavigate={handleSchemeNavigate}
          />
        ) : isSchemeMode.value && schemeId ? (
          <ConceptPane
            onDelete={handleConceptDelete}
            onRefresh={handleRefresh}
          />
        ) : (
          <div class="scheme-workspace__placeholder">
            Select an item to view details
          </div>
        )}
      </div>

      {/* Concept form modal */}
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

      {/* Property form modal */}
      <Modal
        isOpen={isPropertyFormOpen}
        title="New Property"
        onClose={() => setIsPropertyFormOpen(false)}
      >
        <PropertyForm
          projectId={projectId}
          domainClassUri={selectedClassUri.value ?? undefined}
          onSuccess={handlePropertyFormSuccess}
          onCancel={() => setIsPropertyFormOpen(false)}
        />
      </Modal>

      <ExportModal
        isOpen={isExportOpen}
        schemeId={schemeId!}
        schemeTitle={currentScheme.value?.title ?? ""}
        onClose={() => setIsExportOpen(false)}
      />

      <ImportModal
        isOpen={isImportOpen}
        projectId={projectId}
        onClose={() => setIsImportOpen(false)}
        onSuccess={handleImportSuccess}
      />

      <Modal
        isOpen={isSchemeFormOpen}
        title="New Scheme"
        onClose={() => setIsSchemeFormOpen(false)}
      >
        <SchemeForm
          projectId={projectId}
          onSuccess={handleSchemeFormSuccess}
          onCancel={() => setIsSchemeFormOpen(false)}
        />
      </Modal>
    </div>
  );
}
