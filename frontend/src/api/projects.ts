import { api } from "./client";
import type { Project, ProjectCreate, ProjectUpdate } from "../types/models";
import type { ExportFormat } from "./schemes";

export const projectsApi = {
  list: () => api.get<Project[]>("/projects"),

  get: (id: string) => api.get<Project>(`/projects/${id}`),

  create: (data: ProjectCreate) => api.post<Project>("/projects", data),

  update: (id: string, data: ProjectUpdate) =>
    api.put<Project>(`/projects/${id}`, data),

  delete: (id: string) => api.delete(`/projects/${id}`),

  exportVersion: (projectId: string, version: string, format: ExportFormat) =>
    api.getBlob(`/projects/${projectId}/versions/${version}/export?format=${format}`),
};
