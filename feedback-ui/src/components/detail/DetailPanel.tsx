import { useRef, useEffect } from "preact/hooks";
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
  const panelRef = useRef<HTMLElement>(null);

  // Move focus to detail panel when navigating to an entity
  useEffect(() => {
    if (entityKind && entityId && panelRef.current) {
      panelRef.current.focus();
    }
  }, [entityKind, entityId]);

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Tab" && e.shiftKey && e.target === panelRef.current) {
      const active = document.querySelector(
        ".concept-tree__node--active, .sidebar__section-title--active, .data-model-item--active"
      ) as HTMLElement | null;
      if (active) {
        e.preventDefault();
        active.focus();
      }
    }
  }

  if (!entityKind || !entityId) {
    return <WelcomePanel />;
  }

  if (loading.value || !vocabulary.value) {
    return <div class="detail"><LoadingSpinner /></div>;
  }

  let content;
  switch (entityKind) {
    case "concept":
      content = <ConceptDetail key={entityId} conceptId={entityId} />;
      break;
    case "scheme":
      content = <SchemeDetail key={entityId} schemeId={entityId} />;
      break;
    case "class":
      content = <ClassDetail key={entityId} classId={entityId} />;
      break;
    case "property":
      content = <PropertyDetail key={entityId} propertyId={entityId} />;
      break;
    default:
      return <WelcomePanel />;
  }

  return (
    <main ref={panelRef} tabIndex={0} class="detail-panel" aria-label="Entity detail" style="outline: none;" onKeyDown={handleKeyDown}>
      {content}
    </main>
  );
}
