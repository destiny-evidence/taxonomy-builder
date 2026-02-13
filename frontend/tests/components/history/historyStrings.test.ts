import { describe, it, expect } from "vitest";
import { getEntityTypeLabel } from "../../../src/components/history/historyStrings";

describe("historyStrings", () => {
  it("returns 'Property' for property entity type", () => {
    expect(getEntityTypeLabel("property")).toBe("Property");
  });

  it("returns 'Project' for project entity type", () => {
    expect(getEntityTypeLabel("project")).toBe("Project");
  });
});
