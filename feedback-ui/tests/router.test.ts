import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { initRouter, destroyRouter, route, navigate, navigateHome, navigateToProject } from "../src/router";

describe("router", () => {
  beforeEach(() => {
    window.location.hash = "";
    initRouter();
  });

  afterEach(() => {
    destroyRouter();
    window.location.hash = "";
  });

  it("parses empty hash as empty route", () => {
    expect(route.value).toEqual({
      projectId: null,
      version: null,
      entityKind: null,
      entityId: null,
    });
  });

  it("parses project-only route", () => {
    window.location.hash = "/proj-1";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: null,
      entityKind: null,
      entityId: null,
    });
  });

  it("parses concept route", () => {
    window.location.hash = "/proj-1/1.0/concept/abc-123";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: "concept",
      entityId: "abc-123",
    });
  });

  it("parses scheme route", () => {
    window.location.hash = "/proj-1/2.0/scheme/xyz";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "2.0",
      entityKind: "scheme",
      entityId: "xyz",
    });
  });

  it("parses class route", () => {
    window.location.hash = "/proj-1/1.0/class/cls-1";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: "class",
      entityId: "cls-1",
    });
  });

  it("parses property route", () => {
    window.location.hash = "/proj-1/1.0/property/prop-1";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: "property",
      entityId: "prop-1",
    });
  });

  it("returns empty route for invalid hash", () => {
    window.location.hash = "/invalid/path";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    expect(route.value).toEqual({
      projectId: null,
      version: null,
      entityKind: null,
      entityId: null,
    });
  });

  it("navigate sets hash with projectId", () => {
    navigate("proj-1", "1.0", "concept", "abc");
    expect(window.location.hash).toBe("#/proj-1/1.0/concept/abc");
  });

  it("navigateToProject sets hash to project-only route", () => {
    navigateToProject("proj-1");
    expect(window.location.hash).toBe("#/proj-1");
  });

  it("navigateHome clears hash", () => {
    window.location.hash = "/proj-1/1.0/concept/abc";
    navigateHome();
    expect(window.location.hash).toBe("");
  });

  it("strips Keycloak callback params from hash", () => {
    window.location.hash =
      "/proj-1/1.0/concept/abc-123&state=xyz&session_state=foo&code=bar";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: "concept",
      entityId: "abc-123",
    });
  });
});
