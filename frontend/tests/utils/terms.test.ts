import { describe, it, expect } from "vitest";
import { externalPrefix } from "../../src/utils/terms";

const project = {
  namespace: "https://vocab.destiny-evidence.org",
  namespace_prefixes: {
    "": "https://vocab.destiny-evidence.org/",
    gn: "http://www.geonames.org/ontology#",
    evrepo: "https://vocab.evidence-repository.org/",
  },
};

describe("externalPrefix", () => {
  it("is null for project terms", () => {
    expect(externalPrefix("https://vocab.destiny-evidence.org/Location", project)).toBeNull();
  });

  it("returns the bound prefix for external terms", () => {
    expect(externalPrefix("http://www.geonames.org/ontology#name", project)).toBe("gn");
    expect(externalPrefix("https://vocab.evidence-repository.org/name", project)).toBe("evrepo");
  });

  it("falls back to the namespace when no prefix is bound", () => {
    expect(externalPrefix("http://purl.org/dc/terms/title", project)).toBe("http://purl.org/dc/terms/");
  });

  it("is null without a project", () => {
    expect(externalPrefix("http://www.geonames.org/ontology#name", null)).toBeNull();
  });
});

