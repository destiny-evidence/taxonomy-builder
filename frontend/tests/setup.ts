import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/preact";
import "@testing-library/jest-dom/vitest";

// Mock @dnd-kit/core hooks for tests that render TreeView
// These hooks require DndContext which can be tricky in async test scenarios
vi.mock("@dnd-kit/core", async () => {
  const actual = await vi.importActual("@dnd-kit/core");
  return {
    ...actual,
    useDraggable: () => ({
      attributes: {},
      listeners: {},
      setNodeRef: () => {},
      transform: null,
      isDragging: false,
    }),
    useDroppable: () => ({
      setNodeRef: () => {},
      isOver: false,
    }),
  };
});

// Mock HTML dialog element methods for jsdom
HTMLDialogElement.prototype.showModal = function () {
  this.setAttribute("open", "");
};
HTMLDialogElement.prototype.close = function () {
  this.removeAttribute("open");
};

afterEach(() => {
  cleanup();
});
