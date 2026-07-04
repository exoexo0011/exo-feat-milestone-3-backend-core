import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// EXO frontend build + test configuration.
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
    // Split large vendor libraries into their own chunks. The app is loaded
    // locally (Electron), so raise the size hint accordingly.
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
          markdown: ['react-markdown', 'remark-gfm', 'rehype-highlight', 'highlight.js'],
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    css: false,
    restoreMocks: true,
  },
});
