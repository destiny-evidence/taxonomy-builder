import { PUBLISHED_BASE } from "../config";
import { delay, cacheOptions } from "./latency";

// --- Types matching the published JSON schemas ---

export interface ProjectMeta {
  id: string;
  name: string;
  description: string | null;
  namespace: string | null;
}

export interface RootIndexProject {
  id: string;
  name: string;
  description: string | null;
  latest_version: string | null;
}

export interface RootIndex {
  format_version: string;
  projects: RootIndexProject[];
}

export interface ContentSummary {
  schemes: number;
  concepts: number;
  properties: number;
  classes: number;
}

export interface VersionEntry {
  version: string;
  title: string;
  published_at: string;
  publisher: string | null;
  pre_release: boolean;
  previous_version_id: string | null;
  notes: string | null;
  content_summary: ContentSummary;
}

export interface ProjectIndex {
  format_version: string;
  project: ProjectMeta;
  latest_version: string | null;
  versions: VersionEntry[];
}

export interface VocabConcept {
  pref_label: string;
  identifier: string | null;
  uri: string;
  definition: string | null;
  scope_note: string | null;
  alt_labels: string[];
  broader: string[];
  related: string[];
}

export interface VocabScheme {
  id: string;
  title: string;
  description: string | null;
  uri: string;
  top_concepts: string[];
  concepts: Record<string, VocabConcept>;
}

export interface VocabClass {
  id: string;
  identifier: string;
  uri: string;
  label: string;
  description: string | null;
  scope_note: string | null;
}

export interface VocabProperty {
  id: string;
  identifier: string;
  uri: string;
  label: string;
  description: string | null;
  domain_class_uri: string;
  range_scheme_id: string | null;
  range_scheme_uri: string | null;
  range_datatype: string | null;
  range_class: string | null;
  cardinality: "single" | "multiple";
  required: boolean;
}

export interface Vocabulary {
  format_version: string;
  version: string;
  title: string;
  published_at: string;
  publisher: string | null;
  pre_release: boolean;
  previous_version_id: string | null;
  project: ProjectMeta;
  schemes: VocabScheme[];
  classes: VocabClass[];
  properties: VocabProperty[];
}

// --- Fetch helpers ---

async function fetchPublished<T>(path: string): Promise<T> {
  const url = `${PUBLISHED_BASE}${path}`;
  await delay();
  const response = await fetch(url, cacheOptions());
  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }
  return response.json();
}

export function getRootIndex(): Promise<RootIndex> {
  return fetchPublished("/index.json");
}

export function getProjectIndex(projectId: string): Promise<ProjectIndex> {
  return fetchPublished(`/${projectId}/index.json`);
}

export function getVocabulary(
  projectId: string,
  version: string
): Promise<Vocabulary> {
  return fetchPublished(`/${projectId}/${version}/vocabulary.json`);
}
