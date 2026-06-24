import { vi } from "vitest";
import type { ComponentChildren } from "preact";

// Mock SortableContext - just renders children
export function SortableContext({ children }: { children: ComponentChildren }) {
  return <>{children}</>;
}

// Mock useSortable hook
export const useSortable = vi.fn(() => ({
  attributes: {},
  listeners: {},
  setNodeRef: vi.fn(),
  transform: null,
  transition: undefined,
  isDragging: false,
}));

export const verticalListSortingStrategy = vi.fn();

export function arrayMove<T>(array: T[], from: number, to: number): T[] {
  const next = array.slice();
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved);
  return next;
}
