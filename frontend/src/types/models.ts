// ============ Projects ============
export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string | null;
}

export interface ProjectUpdate {
  name?: string;
  description?: string | null;
}

// ============ Concept Schemes ============
export interface ConceptScheme {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  uri: string | null;
  publisher: string | null;
  version: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConceptSchemeCreate {
  title: string;
  description?: string | null;
  uri?: string | null;
  publisher?: string | null;
  version?: string | null;
}

export interface ConceptSchemeUpdate {
  title?: string;
  description?: string | null;
  uri?: string | null;
  publisher?: string | null;
  version?: string | null;
}

// ============ Concepts ============
export interface ConceptBrief {
  id: string;
  scheme_id: string;
  identifier: string | null;
  pref_label: string;
  definition: string | null;
  scope_note: string | null;
  uri: string | null; // Computed from scheme.uri + identifier
  alt_labels: string[];
  created_at: string;
  updated_at: string;
}

export interface Concept extends ConceptBrief {
  broader: ConceptBrief[];
  related: ConceptBrief[];
}

export interface ConceptCreate {
  pref_label: string;
  identifier?: string | null;
  definition?: string | null;
  scope_note?: string | null;
  alt_labels?: string[];
}

export interface ConceptUpdate {
  pref_label?: string;
  identifier?: string | null;
  definition?: string | null;
  scope_note?: string | null;
  alt_labels?: string[];
}

// ============ Tree ============
export interface TreeNode {
  id: string;
  scheme_id: string;
  identifier: string | null;
  pref_label: string;
  definition: string | null;
  scope_note: string | null;
  uri: string | null;
  alt_labels: string[];
  created_at: string;
  updated_at: string;
  narrower: TreeNode[];
}

// Enriched for rendering
export interface RenderNode {
  id: string;
  pref_label: string;
  definition: string | null;
  path: string;
  depth: number;
  hasMultipleParents: boolean;
  otherParentLabels: string[];
  children: RenderNode[];
}
