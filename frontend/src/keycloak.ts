import Keycloak from "keycloak-js";

export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || "https://keycloak.fef.dev",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "taxonomy-builder",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "taxonomy-builder-ui",
});
