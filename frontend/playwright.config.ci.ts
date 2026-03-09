import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for CI environments.
 *
 * - Uses a single worker to avoid parallel DB mutation races.
 * - Starts native macOS backend (uvicorn) and frontend (Next.js) servers.
 * - Assumes local Postgres and Redis are available natively via Homebrew.
 */
export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,
  workers: 1, // Single worker for DB isolation
  retries: 2,
  reporter: [
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'test-results/e2e-junit.xml' }]
  ],

  globalTeardown: require.resolve('./e2e/global-teardown.ts'),
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ],
  webServer: [
    {
      command: 'cd ../backend && ALLOW_DEV_SEED=true ENV=test python -m uvicorn app.main:app --port 8000',
      url: 'http://localhost:8000/api/v1/health',
      reuseExistingServer: true,
      timeout: 30000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:3000',
      reuseExistingServer: true,
      timeout: 30000,
    }
  ],
});
