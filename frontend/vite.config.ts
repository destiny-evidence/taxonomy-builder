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
    allowedHosts: true, // Allow all hosts (localhost, fef.dev, etc.)
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
