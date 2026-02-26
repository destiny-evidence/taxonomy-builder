import { useSignal } from "@preact/signals";
import { navigate, route } from "../../router";
import { selectedVersion, currentProjectId } from "../../state/vocabulary";
import { isAuthenticated } from "../../state/auth";
import { feedbackCountForEntity } from "../../state/feedback";
import type { ConceptTreeNode } from "../../state/vocabulary";

/** Sum feedback counts for a concept node and all its descendants. */
function subtreeFeedbackCount(node: ConceptTreeNode): number {
  let count = feedbackCountForEntity(node.id, "concept");
  for (const child of node.children) {
    count += subtreeFeedbackCount(child);
  }
  return count;
}

interface ConceptTreeNodeProps {
  node: ConceptTreeNode;
  schemeId: string;
}

function TreeNode({ node, schemeId }: ConceptTreeNodeProps) {
  const expanded = useSignal(false);
  const hasChildren = node.children.length > 0;
  const isActive =
    route.value.entityKind === "concept" && route.value.entityId === node.id;

  function handleClick() {
    if (isActive) {
      (document.querySelector(".detail__title") as HTMLElement)?.focus({ preventScroll: true });
      return;
    }
    const version = selectedVersion.value;
    const projectId = currentProjectId.value;
    if (version && projectId) {
      navigate(projectId, version, "concept", node.id);
    }
  }

  function handleToggle(e: Event) {
    e.stopPropagation();
    expanded.value = !expanded.value;
  }

  const displayCount = isAuthenticated.value
    ? (expanded.value ? feedbackCountForEntity(node.id, "concept") : subtreeFeedbackCount(node))
    : 0;

  return (
    <div>
      <div
        class={`concept-tree__node${isActive ? " concept-tree__node--active" : ""}`}
        role="button"
        tabIndex={0}
        aria-expanded={hasChildren ? expanded.value : undefined}
        onClick={handleClick}
        onKeyDown={(e: KeyboardEvent) => { if (e.key === "Enter") handleClick(); if (e.key === " " && hasChildren) { e.preventDefault(); handleToggle(e); } }}
      >
        {hasChildren ? (
          <svg class={`concept-tree__chevron${expanded.value ? " concept-tree__chevron--open" : ""}`} onClick={handleToggle} width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        ) : (
          <span class="concept-tree__toggle-spacer" />
        )}
        <span class="concept-tree__label">{node.label}</span>
        {displayCount > 0 && <span class="sidebar__badge">{displayCount}</span>}
      </div>
      {hasChildren && expanded.value && (
        <div class="concept-tree__children">
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} schemeId={schemeId} />
          ))}
        </div>
      )}
    </div>
  );
}

interface ConceptTreeProps {
  nodes: ConceptTreeNode[];
  schemeId: string;
}

export function ConceptTree({ nodes, schemeId }: ConceptTreeProps) {
  if (nodes.length === 0) {
    return <div class="sidebar__empty">No concepts</div>;
  }

  return (
    <div class="concept-tree">
      {nodes.map((node) => (
        <TreeNode key={node.id} node={node} schemeId={schemeId} />
      ))}
    </div>
  );
}
