import { DndContext, DragEndEvent, DragStartEvent, DragOverEvent } from "@dnd-kit/core";
import { useCallback, useEffect } from "preact/hooks";
import type { ComponentChildren } from "preact";
import {
  isDragging,
  draggedConceptId,
  draggedPath,
  dropTargetId,
  isAltKeyPressed,
  getParentIdFromPath,
} from "../../state/concepts";
import { conceptsApi } from "../../api/concepts";
import type { DragData, DropData } from "../../types/models";

interface TreeDndProviderProps {
  onMoveComplete: () => void;
  children: ComponentChildren;
}

export function TreeDndProvider({ onMoveComplete, children }: TreeDndProviderProps) {
  // Track alt/option key for polyhierarchy
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.altKey) isAltKeyPressed.value = true;
    }
    function handleKeyUp(e: KeyboardEvent) {
      if (!e.altKey) isAltKeyPressed.value = false;
    }

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const data = event.active.data.current as DragData;
    isDragging.value = true;
    draggedConceptId.value = data.conceptId;
    draggedPath.value = data.path;
  }, []);

  const handleDragOver = useCallback((event: DragOverEvent) => {
    if (event.over) {
      const data = event.over.data.current as DropData;
      dropTargetId.value = data.acceptsDrop ? data.conceptId : null;
    } else {
      dropTargetId.value = null;
    }
  }, []);

  const handleDragEnd = useCallback(
    async (event: DragEndEvent) => {
      const { active, over } = event;

      // Reset drag state
      isDragging.value = false;
      draggedConceptId.value = null;
      const dragPath = draggedPath.value;
      draggedPath.value = null;
      dropTargetId.value = null;

      if (!over || !dragPath) return;

      const dragData = active.data.current as DragData;
      const dropData = over.data.current as DropData;

      if (!dropData.acceptsDrop) return;

      const previousParentId = getParentIdFromPath(dragPath);
      const newParentId = dropData.conceptId === "root" ? null : dropData.conceptId;

      // If alt key held, add as additional parent (don't remove previous)
      const effectivePreviousParent = isAltKeyPressed.value ? null : previousParentId;

      try {
        await conceptsApi.moveConcept(dragData.conceptId, newParentId, effectivePreviousParent);
        onMoveComplete();
      } catch (error) {
        console.error("Failed to move concept:", error);
      }
    },
    [onMoveComplete]
  );

  return (
    <DndContext
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      {children}
    </DndContext>
  );
}
