import { computed, signal } from "@preact/signals";
import { keycloak } from "../keycloak";

export interface KeycloakUser {
  sub: string;
  email?: string;
  name?: string;
  preferred_username?: string;
  groups?: string[];
}

export const authInitialized = signal(false);
export const authLoading = signal(false);
export const authError = signal<string | null>(null);
export const currentUser = signal<KeycloakUser | null>(null);

export const isAuthenticated = computed(
  () => authInitialized.value && currentUser.value !== null
);

export const userDisplayName = computed(() => {
  const user = currentUser.value;
  if (!user) return null;
  return user.name || user.preferred_username || user.email || "Unknown";
});

export const userEmail = computed(() => currentUser.value?.email || null);

export function setUserFromKeycloak(): void {
  if (keycloak.tokenParsed) {
    currentUser.value = keycloak.tokenParsed as KeycloakUser;
  }
}

export function clearAuth(): void {
  currentUser.value = null;
  authError.value = null;
}
