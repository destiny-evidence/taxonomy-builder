import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { publishingApi } from "../../src/api/publishing";

describe("publishingApi", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  describe("getPreview", () => {
    it("fetches publish preview for a project", async () => {
      const mockPreview = {
        validation: { valid: true, errors: [] },
        diff: null,
        content_summary: { schemes: 2, concepts: 10, properties: 3 },
        suggested_version: "1.0",
        suggested_pre_release_version: "1.0-pre1",
        latest_version: null,
        latest_pre_release_version: null,
      };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockPreview),
      });

      const result = await publishingApi.getPreview("project-123");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/publish/preview",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockPreview);
    });
  });

  describe("publish", () => {
    it("publishes a new version", async () => {
      const request = {
        version: "1.0",
        title: "First release",
        notes: "Initial publish",
      };
      const mockVersion = { id: "ver-1", version: "1.0", title: "First release" };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: () => Promise.resolve(mockVersion),
      });

      const result = await publishingApi.publish("project-123", request);

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/publish",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify(request),
        })
      );
      expect(result).toEqual(mockVersion);
    });

    it("publishes a pre-release", async () => {
      const request = {
        version: "1.0-pre1",
        title: "Pre-release",
        pre_release: true,
      };
      const mockVersion = { id: "ver-1", version: "1.0-pre1", title: "Pre-release", finalized: false };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: () => Promise.resolve(mockVersion),
      });

      const result = await publishingApi.publish("project-123", request);

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/publish",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify(request),
        })
      );
      expect(result).toEqual(mockVersion);
    });
  });

  describe("listVersions", () => {
    it("fetches all versions for a project", async () => {
      const mockVersions = [
        { id: "ver-2", version: "1.1", finalized: true },
        { id: "ver-1", version: "1.0", finalized: true },
      ];
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockVersions),
      });

      const result = await publishingApi.listVersions("project-123");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/versions",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockVersions);
    });
  });
});
