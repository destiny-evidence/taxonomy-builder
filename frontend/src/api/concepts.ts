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

  addRelated: (id: string, relatedId: string) =>
    api.post<{ status: string }>(`/concepts/${id}/related`, {
      related_concept_id: relatedId,
    }),

  removeRelated: (id: string, relatedId: string) =>
    api.delete(`/concepts/${id}/related/${relatedId}`),

  moveConcept: (id: string, newParentId: string | null, previousParentId: string | null) =>
    api.post<Concept>(`/concepts/${id}/move`, {
      new_parent_id: newParentId,
      previous_parent_id: previousParentId,
    }),
};
