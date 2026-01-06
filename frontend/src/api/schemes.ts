import { api } from "./client";
import type {
  ConceptScheme,
  ConceptSchemeCreate,
  ConceptSchemeUpdate,
} from "../types/models";

export const schemesApi = {
  listForProject: (projectId: string) =>
    api.get<ConceptScheme[]>(`/projects/${projectId}/schemes`),

  get: (id: string) => api.get<ConceptScheme>(`/schemes/${id}`),

  create: (projectId: string, data: ConceptSchemeCreate) =>
    api.post<ConceptScheme>(`/projects/${projectId}/schemes`, data),

  update: (id: string, data: ConceptSchemeUpdate) =>
    api.put<ConceptScheme>(`/schemes/${id}`, data),

  delete: (id: string) => api.delete(`/schemes/${id}`),
};
