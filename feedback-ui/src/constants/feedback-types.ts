export interface FeedbackTypeOption {
  value: string;
  label: string;
}

const CONCEPT_SCHEME_TYPES: FeedbackTypeOption[] = [
  { value: "unclear_definition", label: "Unclear definition" },
  { value: "missing_term", label: "Missing term/area" },
  { value: "scope_question", label: "Scope question" },
  { value: "overlap_duplication", label: "Overlap/duplication" },
  { value: "general_comment", label: "General comment" },
];

const CLASS_PROPERTY_TYPES: FeedbackTypeOption[] = [
  { value: "incorrect_modelling", label: "Incorrect modelling" },
  { value: "missing_relationship", label: "Missing relationship" },
  { value: "structural_question", label: "Structural question" },
  { value: "general_comment", label: "General comment" },
];

export function getFeedbackTypes(entityType: string): FeedbackTypeOption[] {
  switch (entityType) {
    case "concept":
    case "scheme":
      return CONCEPT_SCHEME_TYPES;
    case "class":
    case "property":
      return CLASS_PROPERTY_TYPES;
    default:
      return CONCEPT_SCHEME_TYPES;
  }
}
