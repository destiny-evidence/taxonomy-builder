import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { propertiesApi } from "../../src/api/properties";

describe("propertiesApi", () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockFetch.mockReset();
  });

  describe("listForProject", () => {
    it("fetches properties for a project", async () => {
      const mockProperties = [
        { id: "prop-1", identifier: "birthDate", label: "Birth Date" },
        { id: "prop-2", identifier: "name", label: "Name" },
      ];
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockProperties),
      });

      const result = await propertiesApi.listForProject("project-123");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/properties",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockProperties);
    });
  });

  describe("get", () => {
    it("fetches a single property by ID", async () => {
      const mockProperty = { id: "prop-1", identifier: "birthDate", label: "Birth Date" };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockProperty),
      });

      const result = await propertiesApi.get("prop-1");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/properties/prop-1",
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual(mockProperty);
    });
  });

  describe("create", () => {
    it("creates a new property for a project", async () => {
      const newProperty = {
        identifier: "birthDate",
        label: "Birth Date",
        domain_class: "http://example.org/Person",
        range_datatype: "xsd:date",
        cardinality: "single" as const,
        required: false,
      };
      const createdProperty = { id: "prop-new", ...newProperty };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: () => Promise.resolve(createdProperty),
      });

      const result = await propertiesApi.create("project-123", newProperty);

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/projects/project-123/properties",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify(newProperty),
        })
      );
      expect(result).toEqual(createdProperty);
    });
  });

  describe("update", () => {
    it("updates an existing property", async () => {
      const updates = { label: "Date of Birth" };
      const updatedProperty = { id: "prop-1", identifier: "birthDate", label: "Date of Birth" };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(updatedProperty),
      });

      const result = await propertiesApi.update("prop-1", updates);

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/properties/prop-1",
        expect.objectContaining({
          method: "PUT",
          body: JSON.stringify(updates),
        })
      );
      expect(result).toEqual(updatedProperty);
    });
  });

  describe("delete", () => {
    it("deletes a property", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
      });

      await propertiesApi.delete("prop-1");

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/properties/prop-1",
        expect.objectContaining({ method: "DELETE" })
      );
    });
  });
});
