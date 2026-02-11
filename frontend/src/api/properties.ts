import { api } from "./client";
import type {
  Property,
  PropertyCreate,
  PropertyUpdate,
  CoreOntologyResponse,
} from "../types/models";

export const propertiesApi = {
  listForProject: (projectId: string) =>
    api.get<Property[]>(`/projects/${projectId}/properties`),

  get: (id: string) => api.get<Property>(`/properties/${id}`),

  create: (projectId: string, data: PropertyCreate) =>
    api.post<Property>(`/projects/${projectId}/properties`, data),

  update: (id: string, data: PropertyUpdate) =>
    api.put<Property>(`/properties/${id}`, data),

  delete: (id: string) => api.delete(`/properties/${id}`),
};

export const ontologyApi = {
  get: () => api.get<CoreOntologyResponse>("/ontology"),
};
