import { useState, useEffect } from "preact/hooks";
import { conceptsApi } from "../../api/concepts";
import { TreeView } from "../tree/TreeView";
import type { TreeNode } from "../../types/models";
import "./SchemePreview.css";

interface SchemePreviewProps {
  schemeId: string;
}

export function SchemePreview({ schemeId }: SchemePreviewProps) {
  const [treeData, setTreeData] = useState<TreeNode[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTree() {
      setLoading(true);
      setError(null);
      try {
        const data = await conceptsApi.getTree(schemeId);
        setTreeData(data);
      } catch (err) {
        setError("Failed to load scheme");
        console.error("Failed to load scheme tree:", err);
      } finally {
        setLoading(false);
      }
    }
    loadTree();
  }, [schemeId]);

  if (loading) {
    return <div class="scheme-preview__loading">Loading...</div>;
  }

  if (error) {
    return <div class="scheme-preview__error">{error}</div>;
  }

  if (!treeData || treeData.length === 0) {
    return <div class="scheme-preview__empty">No concepts in this scheme.</div>;
  }

  return (
    <div class="scheme-preview">
      <TreeView schemeId={schemeId} treeData={treeData} readOnly />
    </div>
  );
}
