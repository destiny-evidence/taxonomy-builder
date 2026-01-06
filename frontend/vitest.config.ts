import { defineConfig } from "vitest/config";
import preact from "@preact/preset-vite";
import { resolve } from "path";

export default defineConfig({
  plugins: [preact()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
      // Alias react to preact/compat for @dnd-kit compatibility
      "react": resolve(__dirname, "node_modules/preact/compat"),
      "react-dom": resolve(__dirname, "node_modules/preact/compat"),
      "react/jsx-runtime": resolve(__dirname, "node_modules/preact/jsx-runtime"),
      // Mock @dnd-kit in tests to avoid React compatibility issues
      "@dnd-kit/core": resolve(__dirname, "tests/__mocks__/@dnd-kit/core.tsx"),
    },
    dedupe: ["preact"],
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
  },
});
