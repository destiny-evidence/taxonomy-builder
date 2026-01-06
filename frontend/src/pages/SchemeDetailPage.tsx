import { useEffect, useState } from "preact/hooks";
import { Breadcrumb } from "../components/layout/Breadcrumb";
import { TreeView } from "../components/tree/TreeView";
import { TreeControls } from "../components/tree/TreeControls";
import { ConceptDetail } from "../components/concepts/ConceptDetail";
import { ConceptForm } from "../components/concepts/ConceptForm";
import { Modal } from "../components/common/Modal";
import { Button } from "../components/common/Button";
import { currentProject } from "../state/projects";
import { currentScheme } from "../state/schemes";
import {
  concepts,
  treeData,
  treeLoading,
  selectedConceptId,
  selectedConcept,
  expandedPaths,
} from "../state/concepts";
import { projectsApi } from "../api/projects";
import { schemesApi } from "../api/schemes";
import { conceptsApi } from "../api/concepts";
import type { Concept } from "../types/models";
import "./SchemeDetailPage.css";

interface SchemeDetailPageProps {
  path?: string;
  schemeId?: string;
}

export function SchemeDetailPage({ schemeId }: SchemeDetailPageProps) {
  const [loading, setLoading] = useState(true);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingConcept, setEditingConcept] = useState<Concept | null>(null);
  const [formKey, setFormKey] = useState(0);

  useEffect(() => {
    if (schemeId) {
      loadScheme(schemeId);
      loadTree(schemeId);
      loadConcepts(schemeId);
    }
    return () => {
      selectedConceptId.value = null;
    };
  }, [schemeId]);

  async function loadScheme(id: string) {
    try {
      const scheme = await schemesApi.get(id);
      currentScheme.value = scheme;
      // Also load the parent project
      const project = await projectsApi.get(scheme.project_id);
      currentProject.value = project;
    } catch (err) {
      console.error("Failed to load scheme:", err);
    } finally {
      setLoading(false);
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

  function handleCreate() {
    setEditingConcept(null);
    setFormKey((k) => k + 1); // Force form reset
    setIsFormOpen(true);
  }

  function handleEdit(concept: Concept) {
    setEditingConcept(concept);
    setIsFormOpen(true);
  }

  function handleFormClose() {
    setIsFormOpen(false);
    setEditingConcept(null);
  }

  async function handleFormSuccess() {
    handleFormClose();
    if (schemeId) {
      await Promise.all([loadTree(schemeId), loadConcepts(schemeId)]);
      // Refresh selected concept if it was edited
      if (selectedConceptId.value) {
        const updated = await conceptsApi.get(selectedConceptId.value);
        concepts.value = concepts.value.map((c) =>
          c.id === updated.id ? updated : c
        );
      }
    }
  }

  async function handleDelete(conceptId: string) {
    try {
      await conceptsApi.delete(conceptId);
      selectedConceptId.value = null;
      if (schemeId) {
        await Promise.all([loadTree(schemeId), loadConcepts(schemeId)]);
      }
    } catch (err) {
      console.error("Failed to delete concept:", err);
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

  if (loading) {
    return <div class="scheme-detail__loading">Loading...</div>;
  }

  if (!currentScheme.value) {
    return <div class="scheme-detail__error">Scheme not found</div>;
  }

  const scheme = currentScheme.value;
  const project = currentProject.value;

  return (
    <div class="scheme-detail">
      <Breadcrumb
        items={[
          { label: "Projects", href: "/" },
          { label: project?.name ?? "Project", href: `/projects/${project?.id}` },
          { label: scheme.title },
        ]}
      />

      <div class="scheme-detail__layout">
        <div class="scheme-detail__main">
          <div class="scheme-detail__header">
            <div>
              <h1 class="scheme-detail__title">{scheme.title}</h1>
              {scheme.description && (
                <p class="scheme-detail__description">{scheme.description}</p>
              )}
            </div>
            <Button onClick={handleCreate}>Add Concept</Button>
          </div>

          <TreeControls
            onExpandAll={handleExpandAll}
            onCollapseAll={handleCollapseAll}
          />

          <TreeView schemeId={schemeId!} />
        </div>

        <aside class="scheme-detail__sidebar">
          {selectedConcept.value ? (
            <ConceptDetail
              concept={selectedConcept.value}
              onEdit={() => handleEdit(selectedConcept.value!)}
              onDelete={() => handleDelete(selectedConcept.value!.id)}
              onRefresh={async () => {
                if (schemeId) {
                  await Promise.all([loadTree(schemeId), loadConcepts(schemeId)]);
                  // Refresh selected concept to get updated broader relationships
                  if (selectedConceptId.value) {
                    const updated = await conceptsApi.get(selectedConceptId.value);
                    concepts.value = concepts.value.map((c) =>
                      c.id === updated.id ? updated : c
                    );
                  }
                }
              }}
            />
          ) : (
            <div class="scheme-detail__sidebar-empty">
              Select a concept to view details
            </div>
          )}
        </aside>
      </div>

      <Modal
        isOpen={isFormOpen}
        title={editingConcept ? "Edit Concept" : "New Concept"}
        onClose={handleFormClose}
      >
        <ConceptForm
          key={editingConcept?.id ?? formKey}
          schemeId={schemeId!}
          concept={editingConcept}
          onSuccess={handleFormSuccess}
          onCancel={handleFormClose}
        />
      </Modal>
    </div>
  );
}
