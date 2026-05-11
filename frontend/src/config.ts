export const API_BASE = import.meta.env.VITE_API_BASE || "/api";
export const FEEDBACK_URL =
  import.meta.env.VITE_FEEDBACK_URL ||
  (import.meta.env.DEV ? "http://localhost:3001" : "");
export const MATOMO_CONTAINER_URL = import.meta.env.VITE_MATOMO_CONTAINER_URL;
