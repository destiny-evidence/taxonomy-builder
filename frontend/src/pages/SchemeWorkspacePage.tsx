import { useEffect, useState } from "preact/hooks";
import { route } from "preact-router";
import { SchemesPane } from "../components/workspace/SchemesPane";
import { TreePane } from "../components/workspace/TreePane";
import { ConceptPane } from "../components/workspace/ConceptPane";
import { PropertiesPane } from "../components/properties/PropertiesPane";
import { PropertyForm } from "../components/properties/PropertyForm";
import { ConceptForm } from "../components/concepts/ConceptForm";
import { SchemeForm } from "../components/schemes/SchemeForm";
import { ExportModal } from "../components/schemes/ExportModal";
import { ImportModal } from "../components/schemes/ImportModal";
import { Modal } from "../components/common/Modal";
import { ConfirmDialog } from "../components/common/ConfirmDialog";
import { projects } from "../state/projects";
import { schemes, currentScheme } from "../state/schemes";
import { currentProject } from "../state/projects";
import {
  properties,
  propertiesLoading,
  propertiesError,
  coreOntology,
  coreOntologyLoading,
} from "../state/properties";
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
import { propertiesApi, ontologyApi } from "../api/properties";
import type { Concept, Property } from "../types/models";
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
  const [editingConcept, setEditingConcept] = useState<Concept | null>(null);
  const [initialBroaderId, setInitialBroaderId] = useState<string | null>(null);
  const [formKey, setFormKey] = useState(0);

  // Property modal state
  const [isPropertyFormOpen, setIsPropertyFormOpen] = useState(false);
  const [editingProperty, setEditingProperty] = useState<Property | null>(null);
  const [deletingProperty, setDeletingProperty] = useState<Property | null>(null);
  const [propertyFormKey, setPropertyFormKey] = useState(0);

  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
      loadSchemes(projectId);
      loadProperties(projectId);
      loadOntology();
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

  async function loadProperties(projectId: string) {
    propertiesLoading.value = true;
    propertiesError.value = null;
    try {
      properties.value = await propertiesApi.listForProject(projectId);
    } catch (err) {
      const message = err instanceof Error ? err.message : "An error occurred";
      propertiesError.value = message;
      console.error("Failed to load properties:", err);
    } finally {
      propertiesLoading.value = false;
    }
  }

  async function loadOntology() {
    if (coreOntology.value) return; // cached
    coreOntologyLoading.value = true;
    try {
      coreOntology.value = await ontologyApi.get();
    } catch (err) {
      console.error("Failed to load ontology:", err);
    } finally {
      coreOntologyLoading.value = false;
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

  function handlePropertiesSelect() {
    route(`/projects/${projectId}`);
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

  // Property handlers
  function handlePropertyCreate() {
    setEditingProperty(null);
    setPropertyFormKey((k) => k + 1);
    setIsPropertyFormOpen(true);
  }

  function handlePropertyEdit(property: Property) {
    setEditingProperty(property);
    setPropertyFormKey((k) => k + 1);
    setIsPropertyFormOpen(true);
  }

  function handlePropertyFormClose() {
    setIsPropertyFormOpen(false);
    setEditingProperty(null);
  }

  async function handlePropertyFormSuccess() {
    handlePropertyFormClose();
    if (projectId) {
      await loadProperties(projectId);
    }
  }

  function handlePropertyDeleteRequest(property: Property) {
    setDeletingProperty(property);
  }

  async function handlePropertyDeleteConfirm() {
    if (deletingProperty && projectId) {
      try {
        await propertiesApi.delete(deletingProperty.id);
        setDeletingProperty(null);
        await loadProperties(projectId);
      } catch (err) {
        console.error("Failed to delete property:", err);
      }
    }
  }

  if (!projectId) {
    return <div>Project ID required</div>;
  }

  const showProperties = !schemeId;
  const ontologyClasses = coreOntology.value?.classes ?? [];

  return (
    <div class="scheme-workspace">
      <SchemesPane
        projectId={projectId}
        currentSchemeId={schemeId ?? null}
        showProperties={showProperties}
        onSchemeSelect={handleSchemeSelect}
        onPropertiesSelect={handlePropertiesSelect}
        onNewScheme={() => setIsSchemeFormOpen(true)}
        onImport={() => setIsImportOpen(true)}
      />

      <div class={schemeId ? "scheme-workspace__main" : "scheme-workspace__main--wide"}>
        {schemeId ? (
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
          <PropertiesPane
            projectId={projectId}
            properties={properties.value}
            schemes={schemes.value}
            ontologyClasses={ontologyClasses}
            loading={propertiesLoading.value}
            error={propertiesError.value}
            onCreate={handlePropertyCreate}
            onEdit={handlePropertyEdit}
            onDelete={handlePropertyDeleteRequest}
          />
        )}
      </div>

      {schemeId && (
        <div class="scheme-workspace__detail">
          <ConceptPane
            onDelete={handleDelete}
            onRefresh={handleRefresh}
          />
        </div>
      )}

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

      <Modal
        isOpen={isPropertyFormOpen}
        title={editingProperty ? "Edit Property" : "New Property"}
        onClose={handlePropertyFormClose}
      >
        <PropertyForm
          key={editingProperty?.id ?? propertyFormKey}
          projectId={projectId}
          schemes={schemes.value}
          ontologyClasses={ontologyClasses}
          property={editingProperty}
          onSuccess={handlePropertyFormSuccess}
          onCancel={handlePropertyFormClose}
        />
      </Modal>

      <ConfirmDialog
        isOpen={!!deletingProperty}
        title="Delete Property"
        message={`Are you sure you want to delete "${deletingProperty?.label}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        onConfirm={handlePropertyDeleteConfirm}
        onCancel={() => setDeletingProperty(null)}
      />
    </div>
  );
}
