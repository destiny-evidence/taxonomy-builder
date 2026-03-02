import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { classesApi } from "../../src/api/classes";

describe("classesApi", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  describe("listForProject", () => {
    it("fetches classes for a project", async () => {
      const mockClasses = [
        {
          id: "1",
          project_id: "project-123",
          identifier: "Person",
          uri: "http://example.org/Person",
          label: "Person",
          description: "A human being",
          scope_note: null,
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        },
      ];
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockClasses),
      });

      const result = await classesApi.listForProject("project-123");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/classes",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockClasses);
    });
  });

  describe("get", () => {
    it("fetches a single class by id", async () => {
      const mockClass = {
        id: "cls-1",
        project_id: "project-123",
        identifier: "Person",
        uri: "http://example.org/Person",
        label: "Person",
        description: "A human being",
        scope_note: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockClass),
      });

      const result = await classesApi.get("cls-1");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/classes/cls-1",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockClass);
    });
  });

  describe("create", () => {
    it("creates a class in a project", async () => {
      const mockClass = {
        id: "cls-new",
        project_id: "project-123",
        identifier: "Finding",
        uri: "http://example.org/Finding",
        label: "Finding",
        description: "A research finding",
        scope_note: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: () => Promise.resolve(mockClass),
      });

      const result = await classesApi.create("project-123", {
        identifier: "Finding",
        label: "Finding",
        description: "A research finding",
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/classes",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            identifier: "Finding",
            label: "Finding",
            description: "A research finding",
          }),
        })
      );
      expect(result).toEqual(mockClass);
    });
  });

  describe("update", () => {
    it("updates a class", async () => {
      const mockClass = {
        id: "cls-1",
        project_id: "project-123",
        identifier: "Person",
        uri: "http://example.org/Person",
        label: "Person (Updated)",
        description: "Updated description",
        scope_note: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-02T00:00:00Z",
      };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockClass),
      });

      const result = await classesApi.update("cls-1", {
        label: "Person (Updated)",
        description: "Updated description",
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/classes/cls-1",
        expect.objectContaining({
          method: "PUT",
          body: JSON.stringify({
            label: "Person (Updated)",
            description: "Updated description",
          }),
        })
      );
      expect(result).toEqual(mockClass);
    });
  });

  describe("delete", () => {
    it("deletes a class", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      });

      await classesApi.delete("cls-1");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/classes/cls-1",
        expect.objectContaining({ method: "DELETE" })
      );
    });
  });
});
