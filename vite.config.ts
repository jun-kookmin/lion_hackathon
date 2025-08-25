import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Vercel 환경에서는 Replit 관련 플러그인 불필요
const plugins = [react()];

export default defineConfig({
  base: "/",

  root: path.resolve(__dirname, "client"), // client 폴더를 프로젝트 루트로 지정
  plugins,

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "client", "src"),
      "@shared": path.resolve(__dirname, "shared"),
      "@assets": path.resolve(__dirname, "attached_assets"),
    },
  },

  build: {
    outDir: path.resolve(__dirname, "dist"), // dist 폴더를 루트에 생성
    emptyOutDir: true,
  },

  server: {
    fs: {
      strict: true,
      deny: ["**/.*"],
    },
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000", // 로컬 개발 시 Django 백엔드로 프록시
        changeOrigin: true,
      },
    },
  },
});
