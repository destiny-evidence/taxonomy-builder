import { defineConfig } from "vite";
import { resolve } from "path";

/**
 * Separate Vite build config for the service worker.
 *
 * The service worker must be built as a standalone file (not part of
 * the main app bundle) because it runs in a separate context.
 * This config builds src/sw.ts → dist/sw.js.
 */
export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "src/sw.ts"),
      formats: ["es"],
      fileName: () => "sw.js",
    },
    outDir: "dist",
    emptyOutDir: false,
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
});
