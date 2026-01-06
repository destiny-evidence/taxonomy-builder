import { api } from "./client";
import type {
  Concept,
  ConceptCreate,
  ConceptUpdate,
  TreeNode,
} from "../types/models";

export const conceptsApi = {
  listForScheme: (schemeId: string) =>
    api.get<Concept[]>(`/schemes/${schemeId}/concepts`),

  getTree: (schemeId: string) => api.get<TreeNode[]>(`/schemes/${schemeId}/tree`),

  get: (id: string) => api.get<Concept>(`/concepts/${id}`),

  create: (schemeId: string, data: ConceptCreate) =>
    api.post<Concept>(`/schemes/${schemeId}/concepts`, data),

  update: (id: string, data: ConceptUpdate) =>
    api.put<Concept>(`/concepts/${id}`, data),

  delete: (id: string) => api.delete(`/concepts/${id}`),

  addBroader: (id: string, broaderId: string) =>
    api.post<{ status: string }>(`/concepts/${id}/broader`, {
      broader_concept_id: broaderId,
    }),

  removeBroader: (id: string, broaderId: string) =>
    api.delete(`/concepts/${id}/broader/${broaderId}`),
};
