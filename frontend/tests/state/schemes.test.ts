import { describe, it, expect } from "vitest";
import { reorderSchemes } from "../../src/state/schemes";
import type { ConceptScheme } from "../../src/types/models";

function makeScheme(
  id: string,
  projectId: string,
  position: number,
): ConceptScheme {
  return {
    id,
    project_id: projectId,
    title: id,
    description: null,
    uri: null,
    position,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  };
}

describe("reorderSchemes", () => {
  const a = makeScheme("a", "p1", 0);
  const b = makeScheme("b", "p1", 1);
  const c = makeScheme("c", "p1", 2);

  it("moves an item down and renumbers positions", () => {
    const result = reorderSchemes([a, b, c], "p1", "a", "c");
    expect(result).not.toBeNull();
    expect(result!.newIndex).toBe(2);
    expect(result!.schemes.map((s) => s.id)).toEqual(["b", "c", "a"]);
    expect(result!.schemes.map((s) => s.position)).toEqual([0, 1, 2]);
  });

  it("moves an item up and renumbers positions", () => {
    const result = reorderSchemes([a, b, c], "p1", "c", "a");
    expect(result).not.toBeNull();
    expect(result!.newIndex).toBe(0);
    expect(result!.schemes.map((s) => s.id)).toEqual(["c", "a", "b"]);
    expect(result!.schemes.map((s) => s.position)).toEqual([0, 1, 2]);
  });

  it("returns null when dropped on itself", () => {
    expect(reorderSchemes([a, b, c], "p1", "a", "a")).toBeNull();
  });

  it("leaves other projects' schemes untouched", () => {
    const x = makeScheme("x", "p2", 0);
    const y = makeScheme("y", "p2", 1);
    const result = reorderSchemes([a, x, b, y, c], "p1", "a", "c");
    expect(result).not.toBeNull();
    const p2 = result!.schemes.filter((s) => s.project_id === "p2");
    expect(p2.map((s) => s.id)).toEqual(["x", "y"]);
    expect(p2.map((s) => s.position)).toEqual([0, 1]);
    const p1 = result!.schemes.filter((s) => s.project_id === "p1");
    expect(p1.map((s) => s.id)).toEqual(["b", "c", "a"]);
  });
});
