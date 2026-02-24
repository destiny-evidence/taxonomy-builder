import { afterEach } from "vitest";
import { cleanup } from "@testing-library/preact";
import "@testing-library/jest-dom/vitest";

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
