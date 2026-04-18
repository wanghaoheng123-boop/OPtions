import { defineConfig, devices } from '@playwright/test';

/**
 * E2E runs against Vite preview with /api routes mocked in tests (no Python backend required).
 * Local: `npm run build && npm run test:e2e` from frontend/
 */
export default defineConfig({
  testDir: 'e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
    ...devices['Desktop Chrome'],
  },
  webServer: process.env.PW_NO_WEBSERVER
    ? undefined
    : {
        command: 'npm run build && vite preview --host 127.0.0.1 --strictPort --port 4173',
        url: 'http://127.0.0.1:4173',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
