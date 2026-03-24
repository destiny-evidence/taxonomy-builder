import { describe, it, expect } from "vitest";
import { extractLocalName } from "../../src/utils/strings";

describe("extractLocalName", () => {
  it("extracts local name from slash-separated URI", () => {
    expect(extractLocalName("https://example.org/vocab/Finding")).toBe("Finding");
  });

  it("extracts local name from hash-separated URI", () => {
    expect(extractLocalName("http://www.w3.org/2002/07/owl#Thing")).toBe("Thing");
  });

  it("extracts local name from nested path URI", () => {
    expect(extractLocalName("https://example.org/vocab/nested/path/Class")).toBe("Class");
  });

  it("prefers hash over slash when hash comes last", () => {
    expect(extractLocalName("https://example.org/vocab#LocalName")).toBe("LocalName");
  });

  it("prefers slash over hash when slash comes last", () => {
    // Unusual but valid — slash after hash
    expect(extractLocalName("https://example.org/vocab#ns/Name")).toBe("Name");
  });

  it("returns empty string for URI ending in slash", () => {
    expect(extractLocalName("https://example.org/")).toBe("");
  });

  it("returns full string when no slash or hash exists", () => {
    expect(extractLocalName("urn:isbn:0451450523")).toBe("urn:isbn:0451450523");
  });

  it("handles W3C XSD namespace URIs", () => {
    expect(extractLocalName("http://www.w3.org/2001/XMLSchema#string")).toBe("string");
    expect(extractLocalName("http://www.w3.org/2001/XMLSchema#decimal")).toBe("decimal");
  });
});
