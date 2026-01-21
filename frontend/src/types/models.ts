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

// Match status for search filtering
export type MatchStatus = "none" | "match" | "ancestor";

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
  matchStatus: MatchStatus;
}

// ============ Drag and Drop ============
export interface ConceptMoveRequest {
  new_parent_id: string | null;
  previous_parent_id: string | null;
}

export interface DragData {
  conceptId: string;
  currentParentId: string | null;
  path: string;
}

export interface DropData {
  conceptId: string;
  acceptsDrop: boolean;
}

// ============ History ============
export interface ChangeEvent {
  id: string;
  timestamp: string;
  entity_type: string;
  entity_id: string;
  scheme_id: string | null;
  action: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  user_id: string | null;
}

// ============ Published Versions ============
export interface PublishedVersion {
  id: string;
  scheme_id: string;
  version_label: string;
  published_at: string;
  snapshot: Record<string, unknown>;
  notes: string | null;
}

export interface PublishedVersionCreate {
  version_label: string;
  notes?: string | null;
}
