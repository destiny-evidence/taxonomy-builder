import { api } from "./client";

// ============ Types ============

export interface ValidationError {
  code: string;
  message: string;
  entity_type: string | null;
  entity_id: string | null;
  entity_label: string | null;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

export interface DiffItem {
  id: string | null;
  uri: string | null;
  label: string;
  entity_type: string;
}

export interface FieldChange {
  field: string;
  old: string | null;
  new: string | null;
}

export interface ModifiedItem {
  id: string;
  label: string;
  entity_type: string;
  changes: FieldChange[];
}

export interface DiffResult {
  added: DiffItem[];
  modified: ModifiedItem[];
  removed: DiffItem[];
}

export interface ContentSummary {
  schemes: number;
  concepts: number;
  properties: number;
}

export interface PublishPreview {
  validation: ValidationResult;
  diff: DiffResult | null;
  content_summary: ContentSummary;
  suggested_version: string | null;
  suggested_pre_release_version: string | null;
  latest_version: string | null;
  latest_pre_release_version: string | null;
}

export interface PublishRequest {
  version: string;
  title: string;
  notes?: string | null;
  pre_release?: boolean;
}

export interface PublishedVersionRead {
  id: string;
  project_id: string;
  version: string;
  title: string;
  notes: string | null;
  finalized: boolean;
  published_at: string | null;
  publisher: string | null;
  latest: boolean;
  previous_version_id: string | null;
}

// ============ API ============

export const publishingApi = {
  getPreview: (projectId: string) =>
    api.get<PublishPreview>(`/projects/${projectId}/publish/preview`),

  publish: (projectId: string, data: PublishRequest) =>
    api.post<PublishedVersionRead>(`/projects/${projectId}/publish`, data),

  listVersions: (projectId: string) =>
    api.get<PublishedVersionRead[]>(`/projects/${projectId}/versions`),
};
