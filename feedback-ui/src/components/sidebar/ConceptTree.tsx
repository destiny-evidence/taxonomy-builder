import { useSignal } from "@preact/signals";
import { navigate, route } from "../../router";
import { selectedVersion, currentProjectId } from "../../state/vocabulary";
import { isAuthenticated } from "../../state/auth";
import { feedbackCountForEntity } from "../../state/feedback";
import type { ConceptTreeNode } from "../../state/vocabulary";

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

  return (
    <div>
      <div
        class={`concept-tree__node${isActive ? " concept-tree__node--active" : ""}`}
        onClick={handleClick}
      >
        {hasChildren ? (
          <span class="concept-tree__toggle" onClick={handleToggle}>
            {expanded.value ? "▾" : "▸"}
          </span>
        ) : (
          <span class="concept-tree__toggle" />
        )}
        <span class="concept-tree__label">{node.label}</span>
        {isAuthenticated.value && (() => {
          const count = feedbackCountForEntity(node.id, selectedVersion.value ?? "");
          return count > 0 ? <span class="sidebar__badge">{count}</span> : null;
        })()}
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
    <div>
      {nodes.map((node) => (
        <TreeNode key={node.id} node={node} schemeId={schemeId} />
      ))}
    </div>
  );
}
