import { api } from "./client";
import type { Project, ProjectCreate, ProjectUpdate } from "../types/models";

export const projectsApi = {
  list: () => api.get<Project[]>("/projects"),

  get: (id: string) => api.get<Project>(`/projects/${id}`),

  create: (data: ProjectCreate) => api.post<Project>("/projects", data),

  update: (id: string, data: ProjectUpdate) =>
    api.put<Project>(`/projects/${id}`, data),

  delete: (id: string) => api.delete(`/projects/${id}`),
};
