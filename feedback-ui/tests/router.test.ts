import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { initRouter, destroyRouter, route, navigate, navigateHome, navigateToProject } from "../src/router";

describe("router", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/");
    initRouter();
  });

  afterEach(() => {
    destroyRouter();
    window.history.pushState({}, "", "/");
  });

  it("parses root path as empty route", () => {
    expect(route.value).toEqual({
      projectId: null,
      version: null,
      entityKind: null,
      entityId: null,
    });
  });

  it("parses project+version route", () => {
    window.history.pushState({}, "", "/proj-1/1.0");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: null,
      entityId: null,
    });
  });

  it("parses project+version route with trailing slash", () => {
    window.history.pushState({}, "", "/proj-1/1.0/");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: null,
      entityId: null,
    });
  });

  it("parses concept route", () => {
    window.history.pushState({}, "", "/proj-1/1.0/concept/abc-123");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: "concept",
      entityId: "abc-123",
    });
  });

  it("parses scheme route", () => {
    window.history.pushState({}, "", "/proj-1/2.0/scheme/xyz");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "2.0",
      entityKind: "scheme",
      entityId: "xyz",
    });
  });

  it("parses class route", () => {
    window.history.pushState({}, "", "/proj-1/1.0/class/cls-1");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: "class",
      entityId: "cls-1",
    });
  });

  it("parses property route", () => {
    window.history.pushState({}, "", "/proj-1/1.0/property/prop-1");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: "property",
      entityId: "prop-1",
    });
  });

  it("returns versionless project route for single-segment path", () => {
    window.history.pushState({}, "", "/proj-1");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: null,
      entityKind: null,
      entityId: null,
    });
  });

  it("returns empty route for three-segment path without entity kind", () => {
    window.history.pushState({}, "", "/proj-1/1.0/invalid");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(route.value).toEqual({
      projectId: null,
      version: null,
      entityKind: null,
      entityId: null,
    });
  });

  it("navigate pushes state and updates route", () => {
    navigate("proj-1", "1.0", "concept", "abc");
    expect(window.location.pathname).toBe("/proj-1/1.0/concept/abc");
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: "concept",
      entityId: "abc",
    });
  });

  it("navigateToProject pushes state with project+version path", () => {
    navigateToProject("proj-1", "1.0");
    expect(window.location.pathname).toBe("/proj-1/1.0/");
    expect(route.value).toEqual({
      projectId: "proj-1",
      version: "1.0",
      entityKind: null,
      entityId: null,
    });
  });

  it("navigateHome pushes state to root", () => {
    navigate("proj-1", "1.0", "concept", "abc");
    navigateHome();
    expect(window.location.pathname).toBe("/");
    expect(route.value).toEqual({
      projectId: null,
      version: null,
      entityKind: null,
      entityId: null,
    });
  });

  it("responds to popstate (browser back/forward)", () => {
    navigate("proj-1", "1.0", "concept", "abc");
    navigate("proj-1", "1.0", "scheme", "xyz");
    expect(route.value.entityId).toBe("xyz");

    window.history.back();
    // history.back() is async — popstate fires on next tick
    return new Promise<void>((resolve) => {
      window.addEventListener("popstate", () => {
        expect(route.value.entityId).toBe("abc");
        resolve();
      }, { once: true });
    });
  });
});
