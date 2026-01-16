import { cloneElement, isValidElement } from "preact";
import type { ComponentChildren } from "preact";
import { route } from "preact-router";
import { useEffect } from "preact/hooks";
import { isAuthenticated } from "../../state/auth";

interface ProtectedRouteProps {
  children: ComponentChildren;
  path?: string;
  // Route params from preact-router
  [key: string]: unknown;
}

export function ProtectedRoute({
  children,
  path,
  ...routeParams
}: ProtectedRouteProps) {
  useEffect(() => {
    if (!isAuthenticated.value) {
      route("/login", true);
    }
  }, []);

  if (!isAuthenticated.value) {
    return null;
  }

  // Pass route params to children
  if (isValidElement(children)) {
    return cloneElement(children, routeParams);
  }

  return <>{children}</>;
}
