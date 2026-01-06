import { useEffect, useState } from "preact/hooks";
import { Breadcrumb } from "../components/layout/Breadcrumb";
import { ProjectList } from "../components/projects/ProjectList";
import { ProjectForm } from "../components/projects/ProjectForm";
import { Modal } from "../components/common/Modal";
import { Button } from "../components/common/Button";
import { projects, projectsLoading, projectsError } from "../state/projects";
import { projectsApi } from "../api/projects";
import type { Project } from "../types/models";
import "./ProjectsPage.css";

interface ProjectsPageProps {
  path?: string;
}

export function ProjectsPage({}: ProjectsPageProps) {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [formKey, setFormKey] = useState(0);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    projectsLoading.value = true;
    projectsError.value = null;
    try {
      projects.value = await projectsApi.list();
    } catch (err) {
      projectsError.value =
        err instanceof Error ? err.message : "Failed to load projects";
    } finally {
      projectsLoading.value = false;
    }
  }

  function handleCreate() {
    setEditingProject(null);
    setFormKey((k) => k + 1);
    setIsFormOpen(true);
  }

  function handleEdit(project: Project) {
    setEditingProject(project);
    setIsFormOpen(true);
  }

  function handleFormClose() {
    setIsFormOpen(false);
    setEditingProject(null);
  }

  function handleFormSuccess() {
    handleFormClose();
    loadProjects();
  }

  return (
    <div class="projects-page">
      <Breadcrumb items={[{ label: "Projects" }]} />
      <div class="projects-page__content">
        <div class="projects-page__header">
          <h1 class="projects-page__title">Projects</h1>
          <Button onClick={handleCreate}>New Project</Button>
        </div>
        <ProjectList onEdit={handleEdit} onDeleted={loadProjects} />
      </div>

      <Modal
        isOpen={isFormOpen}
        title={editingProject ? "Edit Project" : "New Project"}
        onClose={handleFormClose}
      >
        <ProjectForm
          key={editingProject?.id ?? formKey}
          project={editingProject}
          onSuccess={handleFormSuccess}
          onCancel={handleFormClose}
        />
      </Modal>
    </div>
  );
}
