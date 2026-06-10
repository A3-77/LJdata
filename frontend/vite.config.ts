import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendTarget = env.VITE_DEV_API_PROXY_TARGET || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    build: {
      chunkSizeWarningLimit: 700,
      rollupOptions: {
        output: {
          manualChunks: {
            charts: ["echarts"],
            react: ["react", "react-dom"],
          },
        },
      },
    },
    server: {
      port: 5173,
      proxy: {
        "/api": backendTarget,
      },
    },
  };
});
