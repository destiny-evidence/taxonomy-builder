import { defineConfig } from "vite";
import { resolve } from "path";

/**
 * Separate Vite build config for the service worker.
 *
 * The service worker must be built as a standalone file (not part of
 * the main app bundle) because it runs in a separate context.
 * This config builds src/sw.ts → dist/sw.js.
 */
export default defineConfig(({ mode }) => ({
  build: {
    lib: {
      entry: resolve(__dirname, "src/sw.ts"),
      formats: ["es"],
      fileName: () => "sw.js",
    },
    outDir: "dist",
    emptyOutDir: false,
  },
  define: {
    "process.env.NODE_ENV": JSON.stringify(mode),
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
}));
