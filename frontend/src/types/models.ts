// ============ Projects ============
export interface Project {
  id: string;
  name: string;
  description: string | null;
  namespace: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string | null;
  namespace?: string | null;
}

export interface ProjectUpdate {
  name?: string;
  description?: string | null;
  namespace?: string | null;
}

// ============ Concept Schemes ============
export interface ConceptScheme {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  uri: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConceptSchemeCreate {
  title: string;
  description?: string | null;
  uri?: string | null;
}

export interface ConceptSchemeUpdate {
  title?: string;
  description?: string | null;
  uri?: string | null;
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
  project_id: string | null;
  action: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  user_id: string | null;
  user_display_name: string | null;
}

// ============ Comments ============
export interface User {
  id: string;
  display_name: string;
}

export interface Comment {
  id: string;
  concept_id: string;
  user_id: string;
  parent_comment_id: string | null;
  content: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  resolver: User | null;
  user: User;
  can_delete: boolean;
  replies?: Comment[];  // Nested replies for threaded display
}

export interface CommentCreate {
  content: string;
  parent_comment_id?: string;
}

// ============ Properties ============
// Brief scheme info nested in property responses
export interface ConceptSchemeBrief {
  id: string;
  title: string;
  uri: string | null;
}

export interface Property {
  id: string;
  project_id: string;
  identifier: string;
  label: string;
  description: string | null;
  domain_class: string;
  range_scheme_id: string | null;
  range_scheme: ConceptSchemeBrief | null;
  range_datatype: string | null;
  cardinality: "single" | "multiple";
  required: boolean;
  uri: string | null;
  created_at: string;
  updated_at: string;
}

export interface PropertyCreate {
  identifier: string;
  label: string;
  description?: string | null;
  domain_class: string;
  range_scheme_id?: string | null;
  range_datatype?: string | null;
  cardinality: "single" | "multiple";
  required?: boolean;
}

export interface PropertyUpdate {
  identifier?: string;
  label?: string;
  description?: string | null;
  domain_class?: string;
  range_scheme_id?: string | null;
  range_datatype?: string | null;
  cardinality?: "single" | "multiple";
  required?: boolean;
}

export const DATATYPE_LABELS: Record<string, string> = {
  "xsd:string": "Text",
  "xsd:integer": "Integer",
  "xsd:decimal": "Decimal",
  "xsd:boolean": "Yes / No",
  "xsd:date": "Date",
  "xsd:dateTime": "Date & Time",
  "xsd:anyURI": "URL",
};

export function datatypeLabel(xsdType: string): string {
  return DATATYPE_LABELS[xsdType] ?? xsdType;
}

// ============ Ontology ============
export interface OntologyClass {
  id: string;
  uri: string;
  label: string;
  description: string | null;
}

