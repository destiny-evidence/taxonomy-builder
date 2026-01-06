import type { RenderNode } from "../../types/models";
import "./TreeNode.css";

interface TreeNodeProps {
  node: RenderNode;
  expandedPaths: Set<string>;
  selectedId: string | null;
  onToggle: (path: string) => void;
  onSelect: (conceptId: string) => void;
}

export function TreeNode({
  node,
  expandedPaths,
  selectedId,
  onToggle,
  onSelect,
}: TreeNodeProps) {
  const hasChildren = node.children.length > 0;
  const isExpanded = expandedPaths.has(node.path);
  const isSelected = selectedId === node.id;

  return (
    <div class="tree-node">
      <div
        class={`tree-node__row ${isSelected ? "tree-node__row--selected" : ""}`}
        style={{ paddingLeft: `${node.depth * 20 + 8}px` }}
      >
        {hasChildren ? (
          <button
            class="tree-node__toggle"
            onClick={(e) => {
              e.stopPropagation();
              onToggle(node.path);
            }}
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? "▾" : "▸"}
          </button>
        ) : (
          <span class="tree-node__spacer" />
        )}

        <button
          class="tree-node__label"
          onClick={() => onSelect(node.id)}
          title={node.definition || undefined}
        >
          <span class="tree-node__text">{node.pref_label}</span>
          {node.hasMultipleParents && (
            <span
              class="tree-node__multi-parent"
              title={`Also under: ${node.otherParentLabels.join(", ")}`}
            >
              ⑂
            </span>
          )}
        </button>
      </div>

      {hasChildren && isExpanded && (
        <div class="tree-node__children">
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              expandedPaths={expandedPaths}
              selectedId={selectedId}
              onToggle={onToggle}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
