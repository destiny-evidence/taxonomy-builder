import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { propertiesApi, ontologyApi } from "../../src/api/properties";

vi.mock("../../src/api/auth", () => ({
  getToken: vi.fn(),
}));

vi.mock("../../src/state/auth", () => ({
  clearAuth: vi.fn(),
}));

import { getToken } from "../../src/api/auth";

describe("propertiesApi", () => {
  const mockFetch = vi.fn();
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = mockFetch;
    vi.mocked(getToken).mockResolvedValue("test-token");
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllMocks();
  });

  it("listForProject calls correct endpoint", async () => {
    const mockProperties = [{ id: "p1", label: "Test" }];
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockProperties),
    });

    const result = await propertiesApi.listForProject("proj-1");

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/projects/proj-1/properties");
    expect(result).toEqual(mockProperties);
  });

  it("create sends POST with data", async () => {
    const created = { id: "p1", label: "New Prop" };
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(created),
    });

    const data = {
      identifier: "has-author",
      label: "Has Author",
      domain_class: "http://example.org/Finding",
      range_datatype: "xsd:string",
      cardinality: "single" as const,
      required: false,
    };
    await propertiesApi.create("proj-1", data);

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/projects/proj-1/properties");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body)).toEqual(data);
  });

  it("update sends PUT with data", async () => {
    const updated = { id: "p1", label: "Updated" };
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(updated),
    });

    await propertiesApi.update("p1", { label: "Updated" });

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/properties/p1");
    expect(options.method).toBe("PUT");
  });

  it("delete sends DELETE", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 204,
    });

    await propertiesApi.delete("p1");

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/properties/p1");
    expect(options.method).toBe("DELETE");
  });
});

describe("ontologyApi", () => {
  const mockFetch = vi.fn();
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = mockFetch;
    vi.mocked(getToken).mockResolvedValue("test-token");
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllMocks();
  });

  it("get calls /ontology endpoint", async () => {
    const mockOntology = {
      classes: [{ uri: "http://ex.org/Finding", label: "Finding", comment: null }],
      object_properties: [],
      datatype_properties: [],
    };
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockOntology),
    });

    const result = await ontologyApi.get();

    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/ontology");
    expect(result).toEqual(mockOntology);
  });
});
