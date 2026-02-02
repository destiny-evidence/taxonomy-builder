import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import { resolve } from "path";

export default defineConfig({
  plugins: [preact()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
      // Alias react to preact/compat for @dnd-kit compatibility
      react: "preact/compat",
      "react-dom": "preact/compat",
    },
  },
  server: {
    port: 3000,
    host: "0.0.0.0",
    allowedHosts: [".fef.dev"],
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
