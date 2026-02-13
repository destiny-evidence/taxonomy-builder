import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/preact";
import { GraphView } from "../../../src/components/graph/GraphView";
import { concepts, selectedConceptId } from "../../../src/state/concepts";
import { searchQuery } from "../../../src/state/search";
import { makeConcept } from "../../helpers/factories";

// Mock d3-force to avoid actual simulation in tests
vi.mock("../../../src/components/graph/graphLayout", () => ({
  createSimulation: vi.fn(() => {
    const listeners: Record<string, (() => void)[]> = {};
    return {
      nodes: () => [],
      stop: vi.fn(),
      on: vi.fn((event: string, cb: (() => void) | null) => {
        if (cb) {
          listeners[event] = listeners[event] || [];
          listeners[event].push(cb);
        }
        return this;
      }),
      alpha: vi.fn().mockReturnThis(),
      restart: vi.fn(),
      tick: vi.fn(),
    };
  }),
}));

describe("GraphView", () => {
  beforeEach(() => {
    concepts.value = [];
    selectedConceptId.value = null;
    searchQuery.value = "";
  });

  it("shows empty state when no concepts exist", () => {
    concepts.value = [];
    render(<GraphView />);
    expect(screen.getByText(/no concepts/i)).toBeInTheDocument();
  });

  it("renders without crashing when concepts are present", () => {
    concepts.value = [
      makeConcept({ id: "a", pref_label: "Alpha" }),
      makeConcept({ id: "b", pref_label: "Beta" }),
    ];
    render(<GraphView />);
    const svg = document.querySelector("svg.graph-view");
    expect(svg).toBeInTheDocument();
  });

  it("does not rebuild simulation when selection changes", async () => {
    const { createSimulation } = await import(
      "../../../src/components/graph/graphLayout"
    );

    concepts.value = [
      makeConcept({ id: "a", pref_label: "Alpha" }),
      makeConcept({ id: "b", pref_label: "Beta" }),
    ];

    render(<GraphView />);
    const callCountAfterMount = (createSimulation as ReturnType<typeof vi.fn>).mock.calls.length;

    // Change selection — should NOT rebuild simulation
    selectedConceptId.value = "a";
    await new Promise((r) => setTimeout(r, 50));

    expect((createSimulation as ReturnType<typeof vi.fn>).mock.calls.length).toBe(
      callCountAfterMount,
    );
  });

  it("does not rebuild simulation when search query changes", async () => {
    const { createSimulation } = await import(
      "../../../src/components/graph/graphLayout"
    );

    concepts.value = [
      makeConcept({ id: "a", pref_label: "Alpha" }),
      makeConcept({ id: "b", pref_label: "Beta" }),
    ];

    render(<GraphView />);
    const callCountAfterMount = (createSimulation as ReturnType<typeof vi.fn>).mock.calls.length;

    // Change search — should NOT rebuild simulation
    searchQuery.value = "Alpha";
    await new Promise((r) => setTimeout(r, 50));

    expect((createSimulation as ReturnType<typeof vi.fn>).mock.calls.length).toBe(
      callCountAfterMount,
    );
  });
});
