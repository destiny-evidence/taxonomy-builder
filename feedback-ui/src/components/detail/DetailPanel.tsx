import { route } from "../../router";
import { vocabulary, loading } from "../../state/vocabulary";
import { WelcomePanel } from "./WelcomePanel";
import { ConceptDetail } from "./ConceptDetail";
import { SchemeDetail } from "./SchemeDetail";
import { ClassDetail } from "./ClassDetail";
import { PropertyDetail } from "./PropertyDetail";
import { LoadingSpinner } from "../common/LoadingOverlay";
import "./detail.css";

export function DetailPanel() {
  const { entityKind, entityId } = route.value;

  if (!entityKind || !entityId) {
    return <WelcomePanel />;
  }

  if (loading.value || !vocabulary.value) {
    return <div class="detail"><LoadingSpinner /></div>;
  }

  switch (entityKind) {
    case "concept":
      return <ConceptDetail conceptId={entityId} />;
    case "scheme":
      return <SchemeDetail schemeId={entityId} />;
    case "class":
      return <ClassDetail classId={entityId} />;
    case "property":
      return <PropertyDetail propertyId={entityId} />;
    default:
      return <WelcomePanel />;
  }
}
