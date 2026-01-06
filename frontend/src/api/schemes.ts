import { api } from "./client";
import { API_BASE } from "../config";
import type {
  ConceptScheme,
  ConceptSchemeCreate,
  ConceptSchemeUpdate,
} from "../types/models";

export type ExportFormat = "ttl" | "xml" | "jsonld";

export function getExportUrl(schemeId: string, format: ExportFormat): string {
  return `${API_BASE}/schemes/${schemeId}/export?format=${format}`;
}

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
