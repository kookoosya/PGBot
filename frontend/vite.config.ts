/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { stripCrossorigin } from "./src/vite-strip-crossorigin";

export default defineConfig({
  plugins: [react(), stripCrossorigin()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    modulePreload: {
      polyfill: false,
    },
    rollupOptions: {
      output: {
        manualChunks: {
          leaflet: ["leaflet", "react-leaflet", "leaflet.markercluster"],
          recharts: ["recharts"],
          vendor: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    environmentMatchGlobs: [
      ["src/hooks/**/*.test.ts", "jsdom"],
      ["src/hooks/**/*.test.tsx", "jsdom"],
      ["src/components/**/*.test.tsx", "jsdom"],
    ],
  },
});
