import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// EXO frontend build configuration.
// The dev server proxies API calls to the local FastAPI backend so the
// renderer can use relative URLs in both dev and packaged builds.
export default defineConfig({
  plugins: [react()],
  base: './',
  resolve: {
    alias: { '@': '/src' },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/ws': { target: 'ws://127.0.0.1:8000', ws: true },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
