import { vi } from "vitest";
import type { ComponentChildren } from "preact";

// Mock useDraggable hook
export const useDraggable = vi.fn(() => ({
  attributes: {},
  listeners: {},
  setNodeRef: vi.fn(),
  isDragging: false,
}));

// Mock useDroppable hook
export const useDroppable = vi.fn(() => ({
  setNodeRef: vi.fn(),
  isOver: false,
}));

// Mock DndContext component - just renders children
export function DndContext({ children }: { children: ComponentChildren }) {
  return <>{children}</>;
}

// Export other commonly used items as no-ops
export const DragOverlay = ({ children }: { children: ComponentChildren }) => (
  <>{children}</>
);
