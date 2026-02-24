import Keycloak from "keycloak-js";

export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "taxonomy-builder",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "taxonomy-feedback-ui",
});
