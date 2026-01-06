import { describe, it, expect } from "vitest";
import { getExportUrl } from "../../src/api/schemes";

describe("getExportUrl", () => {
  const schemeId = "abc-123";

  it("builds correct URL for turtle format", () => {
    const url = getExportUrl(schemeId, "ttl");
    expect(url).toBe("/api/schemes/abc-123/export?format=ttl");
  });

  it("builds correct URL for XML format", () => {
    const url = getExportUrl(schemeId, "xml");
    expect(url).toBe("/api/schemes/abc-123/export?format=xml");
  });

  it("builds correct URL for JSON-LD format", () => {
    const url = getExportUrl(schemeId, "jsonld");
    expect(url).toBe("/api/schemes/abc-123/export?format=jsonld");
  });

  it("handles UUIDs as scheme IDs", () => {
    const uuid = "550e8400-e29b-41d4-a716-446655440000";
    const url = getExportUrl(uuid, "ttl");
    expect(url).toBe(`/api/schemes/${uuid}/export?format=ttl`);
  });
});
