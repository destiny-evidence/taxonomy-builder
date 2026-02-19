import { api } from "./client";
import { API_BASE } from "../config";
import type {
  ConceptScheme,
  ConceptSchemeCreate,
  ConceptSchemeUpdate,
} from "../types/models";

export type ExportFormat = "ttl" | "xml" | "jsonld";

// Import types

export interface SchemePreview {
  title: string;
  description: string | null;
  uri: string | null;
  concepts_count: number;
  relationships_count: number;
  warnings: string[];
}

export interface ClassPreview {
  identifier: string;
  label: string;
  uri: string;
}

export interface PropertyPreview {
  identifier: string;
  label: string;
  property_type: string;
  domain_class_uri: string | null;
  range_uri: string | null;
  range_scheme_title: string | null;
}

export interface ImportPreview {
  valid: boolean;
  schemes: SchemePreview[];
  total_concepts_count: number;
  total_relationships_count: number;
  classes: ClassPreview[];
  properties: PropertyPreview[];
  classes_count: number;
  properties_count: number;
  errors: string[];
}

export interface SchemeCreated {
  id: string;
  title: string;
  concepts_created: number;
}

export interface ImportResult {
  schemes_created: SchemeCreated[];
  total_concepts_created: number;
  total_relationships_created: number;
  classes_created: { id: string; identifier: string; label: string }[];
  properties_created: { id: string; identifier: string; label: string }[];
  warnings: string[];
}

export function getExportUrl(schemeId: string, format: ExportFormat): string {
  return `${API_BASE}/schemes/${schemeId}/export?format=${format}`;
}

function importRequest<T>(
  projectId: string,
  file: File,
  dryRun: boolean
): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  return api.postForm<T>(`/projects/${projectId}/import?dry_run=${dryRun}`, formData);
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

  previewImport: (projectId: string, file: File): Promise<ImportPreview> =>
    importRequest<ImportPreview>(projectId, file, true),

  executeImport: (projectId: string, file: File): Promise<ImportResult> =>
    importRequest<ImportResult>(projectId, file, false),
};
