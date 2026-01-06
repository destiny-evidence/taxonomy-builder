import { useEffect, useState } from "preact/hooks";
import { Breadcrumb } from "../components/layout/Breadcrumb";
import { SchemeList } from "../components/schemes/SchemeList";
import { SchemeForm } from "../components/schemes/SchemeForm";
import { Modal } from "../components/common/Modal";
import { Button } from "../components/common/Button";
import { currentProject } from "../state/projects";
import { schemes, schemesLoading, schemesError } from "../state/schemes";
import { projectsApi } from "../api/projects";
import { schemesApi } from "../api/schemes";
import type { ConceptScheme } from "../types/models";
import "./ProjectDetailPage.css";

interface ProjectDetailPageProps {
  path?: string;
  projectId?: string;
}

export function ProjectDetailPage({ projectId }: ProjectDetailPageProps) {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingScheme, setEditingScheme] = useState<ConceptScheme | null>(null);
  const [formKey, setFormKey] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
      loadSchemes(projectId);
    }
  }, [projectId]);

  async function loadProject(id: string) {
    try {
      currentProject.value = await projectsApi.get(id);
    } catch (err) {
      console.error("Failed to load project:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadSchemes(projectId: string) {
    schemesLoading.value = true;
    schemesError.value = null;
    try {
      schemes.value = await schemesApi.listForProject(projectId);
    } catch (err) {
      schemesError.value =
        err instanceof Error ? err.message : "Failed to load schemes";
    } finally {
      schemesLoading.value = false;
    }
  }

  function handleCreate() {
    setEditingScheme(null);
    setFormKey((k) => k + 1);
    setIsFormOpen(true);
  }

  function handleEdit(scheme: ConceptScheme) {
    setEditingScheme(scheme);
    setIsFormOpen(true);
  }

  function handleFormClose() {
    setIsFormOpen(false);
    setEditingScheme(null);
  }

  function handleFormSuccess() {
    handleFormClose();
    if (projectId) {
      loadSchemes(projectId);
    }
  }

  if (loading) {
    return <div class="project-detail__loading">Loading...</div>;
  }

  if (!currentProject.value) {
    return <div class="project-detail__error">Project not found</div>;
  }

  const project = currentProject.value;

  return (
    <div class="project-detail">
      <Breadcrumb
        items={[{ label: "Projects", href: "/" }, { label: project.name }]}
      />
      <div class="project-detail__content">
        <div class="project-detail__header">
          <div>
            <h1 class="project-detail__title">{project.name}</h1>
            {project.description && (
              <p class="project-detail__description">{project.description}</p>
            )}
          </div>
          <Button onClick={handleCreate}>New Scheme</Button>
        </div>

        <h2 class="project-detail__section-title">Concept Schemes</h2>
        <SchemeList
          onEdit={handleEdit}
          onDeleted={() => projectId && loadSchemes(projectId)}
        />
      </div>

      <Modal
        isOpen={isFormOpen}
        title={editingScheme ? "Edit Scheme" : "New Concept Scheme"}
        onClose={handleFormClose}
      >
        <SchemeForm
          key={editingScheme?.id ?? formKey}
          projectId={projectId!}
          scheme={editingScheme}
          onSuccess={handleFormSuccess}
          onCancel={handleFormClose}
        />
      </Modal>
    </div>
  );
}
