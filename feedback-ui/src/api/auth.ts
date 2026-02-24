import { keycloak } from "../keycloak";
import {
  authError,
  authInitialized,
  authLoading,
  clearAuth,
  setUserFromKeycloak,
} from "../state/auth";

/**
 * Initialize Keycloak authentication.
 * Call this once on app startup.
 */
export async function initAuth(): Promise<boolean> {
  authLoading.value = true;
  authError.value = null;

  try {
    const authenticated = await keycloak.init({
      onLoad: "check-sso",
      silentCheckSsoRedirectUri:
        window.location.origin + import.meta.env.BASE_URL + "silent-check-sso.html",
      pkceMethod: "S256",
    });

    if (authenticated) {
      setUserFromKeycloak();
    }

    authInitialized.value = true;
    return authenticated;
  } catch (err) {
    authError.value =
      err instanceof Error ? err.message : "Failed to initialize auth";
    authInitialized.value = true;
    return false;
  } finally {
    authLoading.value = false;
  }
}

/**
 * Redirect to Keycloak login page.
 */
export function login(): void {
  keycloak.login();
}

/**
 * Log out the current user.
 */
export function logout(): void {
  clearAuth();
  keycloak.logout({ redirectUri: window.location.origin + import.meta.env.BASE_URL });
}

/**
 * Get the current access token, refreshing if needed.
 * Returns null if not authenticated.
 */
export async function getToken(): Promise<string | null> {
  if (!keycloak.authenticated) {
    return null;
  }

  try {
    await keycloak.updateToken(30);
    return keycloak.token || null;
  } catch {
    clearAuth();
    return null;
  }
}
