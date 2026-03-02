import { useEffect } from "preact/hooks";
import { route } from "../../router";
import { vocabulary, loading } from "../../state/vocabulary";
import { WelcomePanel } from "./WelcomePanel";
import { ConceptDetail } from "./ConceptDetail";
import { SchemeDetail } from "./SchemeDetail";
import { ClassDetail } from "./ClassDetail";
import { PropertyDetail } from "./PropertyDetail";
import { LoadingSpinner } from "../common/LoadingOverlay";
import { revealEntity } from "../../state/sidebar";
import "./detail.css";

export function DetailPanel() {
  const { entityKind, entityId } = route.value;

  // Reveal entity in sidebar, focus detail title, and reset scroll
  useEffect(() => {
    if (entityKind && entityId) {
      revealEntity(entityKind, entityId);
      const container = document.querySelector(".app-shell__detail");
      if (container) container.scrollTop = 0;
      requestAnimationFrame(() => {
        const title = container?.querySelector(".detail__title") as HTMLElement | null;
        if (title) title.focus({ preventScroll: true });
      });
    }
  }, [entityKind, entityId, vocabulary.value]);

  // Shift+Tab from title returns to active sidebar item
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Tab" && e.shiftKey && (e.target as Element)?.classList?.contains("detail__title")) {
        const active = document.querySelector(
          ".concept-tree__node--active, .sidebar__section-title--active, .data-model-item--active"
        ) as HTMLElement | null;
        if (active) {
          e.preventDefault();
          active.focus();
        }
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  if (!entityKind || !entityId) {
    return <WelcomePanel />;
  }

  if (loading.value || !vocabulary.value) {
    return <div class="detail"><LoadingSpinner /></div>;
  }

  switch (entityKind) {
    case "concept":
      return <ConceptDetail key={entityId} conceptId={entityId} />;
    case "scheme":
      return <SchemeDetail key={entityId} schemeId={entityId} />;
    case "class":
      return <ClassDetail key={entityId} classId={entityId} />;
    case "property":
      return <PropertyDetail key={entityId} propertyId={entityId} />;
    default:
      return <WelcomePanel />;
  }
}
