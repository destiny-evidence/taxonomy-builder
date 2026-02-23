import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { schemesApi } from "../../src/api/schemes";

// Mock the auth module
vi.mock("../../src/api/auth", () => ({
  getToken: vi.fn(),
}));

// Mock the auth state module
vi.mock("../../src/state/auth", () => ({
  clearAuth: vi.fn(),
}));

import { getToken } from "../../src/api/auth";
import { clearAuth } from "../../src/state/auth";

describe("schemesApi.exportScheme", () => {
  const mockFetch = vi.fn();
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = mockFetch;
    vi.mocked(getToken).mockResolvedValue("test-token");
    vi.mocked(clearAuth).mockClear();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllMocks();
  });

  it("fetches with Authorization header and returns blob", async () => {
    const mockBlob = new Blob(["turtle content"], { type: "text/turtle" });
    mockFetch.mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    });

    const result = await schemesApi.exportScheme("abc-123", "ttl");

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/schemes/abc-123/export?format=ttl");
    expect(options.headers?.Authorization).toBe("Bearer test-token");
    expect(result).toBe(mockBlob);
  });
});

describe("schemesApi.previewImport", () => {
  const mockFetch = vi.fn();
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = mockFetch;
    vi.mocked(getToken).mockResolvedValue("test-token");
    vi.mocked(clearAuth).mockClear();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllMocks();
  });

  it("includes Authorization header with Bearer token", async () => {
    const mockPreview = {
      valid: true,
      schemes: [],
      total_concepts_count: 0,
      total_relationships_count: 0,
      errors: [],
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockPreview),
    });

    const file = new File(["test content"], "test.ttl", {
      type: "text/turtle",
    });
    await schemesApi.previewImport("project-123", file);

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/projects/project-123/import?dry_run=true");
    expect(options.method).toBe("POST");
    expect(options.headers?.Authorization).toBe("Bearer test-token");
  });

  it("calls clearAuth on 401 response", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: "Not authenticated" }),
    });

    const file = new File(["test"], "test.ttl");

    await expect(schemesApi.previewImport("project-123", file)).rejects.toThrow(
      "Session expired"
    );
    expect(clearAuth).toHaveBeenCalled();
  });
});
