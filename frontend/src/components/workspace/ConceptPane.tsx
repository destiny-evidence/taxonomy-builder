import { ConceptDetail } from "../concepts/ConceptDetail";
import { selectedConcept } from "../../state/concepts";
import "./ConceptPane.css";

interface ConceptPaneProps {
  onEdit: () => void;
  onDelete: () => void;
  onRefresh: () => void;
}

export function ConceptPane({ onEdit, onDelete, onRefresh }: ConceptPaneProps) {
  const concept = selectedConcept.value;

  if (!concept) {
    return (
      <div class="concept-pane">
        <div class="concept-pane__empty">Select a concept to view details</div>
      </div>
    );
  }

  return (
    <div class="concept-pane">
      <ConceptDetail
        concept={concept}
        onEdit={onEdit}
        onDelete={onDelete}
        onRefresh={onRefresh}
      />
    </div>
  );
}
