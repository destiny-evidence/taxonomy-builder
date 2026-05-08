/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  readonly VITE_FEEDBACK_URL?: string;
  readonly VITE_MATOMO_CONTAINER_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
