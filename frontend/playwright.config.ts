import { defineConfig } from '@playwright/test';

const isCI = Boolean(process.env.CI);

// End-to-end smoke tests. Playwright starts the backend (echo provider) and the
// Vite dev server (which proxies /api and /ws to the backend), then drives a
// headless Chromium against the running app.
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  fullyParallel: false,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: 'python run.py',
      cwd: '../backend',
      url: 'http://127.0.0.1:8000/api/health',
      reuseExistingServer: !isCI,
      timeout: 60_000,
      env: {
        EXO_ENV: 'test',
        EXO_AI_PROVIDER: 'echo',
        EXO_DB_PATH: '../database/e2e.db',
        EXO_LOG_DIR: '../logs',
        EXO_PLUGINS_DIR: '../plugins',
      },
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: !isCI,
      timeout: 60_000,
    },
  ],
});
