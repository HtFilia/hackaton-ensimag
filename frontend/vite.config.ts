import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";
import { existsSync } from "fs";

const adminHtml = resolve(__dirname, "admin.html");

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        student: resolve(__dirname, "index.html"),
        ...(existsSync(adminHtml) ? { admin: adminHtml } : {}),
      },
    },
  },
});
