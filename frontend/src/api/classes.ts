import { api } from "./client";
import type { OntologyClass, OntologyClassCreate, OntologyClassUpdate } from "../types/models";

export const classesApi = {
  listForProject: (projectId: string) =>
    api.get<OntologyClass[]>(`/projects/${projectId}/classes`),

  get: (id: string) => api.get<OntologyClass>(`/classes/${id}`),

  create: (projectId: string, data: OntologyClassCreate) =>
    api.post<OntologyClass>(`/projects/${projectId}/classes`, data),

  update: (id: string, data: OntologyClassUpdate) =>
    api.put<OntologyClass>(`/classes/${id}`, data),

  delete: (id: string) => api.delete(`/classes/${id}`),
};
