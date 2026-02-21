import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: "../src/mcp_server_vegalite_viewer/resources",
    emptyOutDir: false,
    rollupOptions: {
      input: "viewer_app.html",
    },
  },
});
