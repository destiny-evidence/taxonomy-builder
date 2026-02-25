import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import { resolve } from "path";
import { existsSync, readFileSync } from "fs";

/**
 * Dev-only plugin: serve /published/* from the backend blob storage directory.
 * In production, Caddy handles this.
 */
function servePublished() {
  const blobRoot = resolve(__dirname, "../backend/.blob-storage");
  return {
    name: "serve-published",
    configureServer(server: { middlewares: { use: Function } }) {
      server.middlewares.use((req: any, res: any, next: Function) => {
        if (req.url?.startsWith("/published/")) {
          const filePath = resolve(blobRoot, req.url.replace("/published/", ""));
          if (existsSync(filePath)) {
            res.setHeader("Content-Type", "application/json");
            res.end(readFileSync(filePath, "utf-8"));
            return;
          }
        }
        next();
      });
    },
  };
}

export default defineConfig({
  plugins: [preact(), servePublished()],
  base: "/",
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3001,
    host: "0.0.0.0",
    allowedHosts: true,
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
