import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/** 与仓库根目录 `scripts/dev-backend.sh`（默认 8010）对齐；可覆盖，例如 `VITE_DEV_PROXY_TARGET=http://127.0.0.1:8000 npm run dev` */
const devProxyTarget =
  process.env.VITE_DEV_PROXY_TARGET ?? "http://127.0.0.1:8010";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: devProxyTarget,
        changeOrigin: true,
      },
      "/images": {
        target: devProxyTarget,
        changeOrigin: true,
      },
    },
  },
});
