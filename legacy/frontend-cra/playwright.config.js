// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for ft-lineone frontend.
 *
 * Usage:
 *   npx playwright test              # run headless
 *   npx playwright test --headed     # run with browser visible
 *   npx playwright test --ui         # interactive UI mode
 *
 * To run against the production site instead of the local dev server:
 *   PLAYWRIGHT_BASE_URL=https://thelineone.com npx playwright test
 */

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';

export default defineConfig({
  testDir: './tests',
  /* Maximum time one test can run for. */
  timeout: 90 * 1000,
  expect: {
    timeout: 5000,
  },
  /* Run tests in parallel. */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only. */
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL,
    baseURL_user: baseURL,
    collectCodeCoverage: false,
    /* Collect trace when retrying the failed test. */
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Uncomment to test more browsers:
    // { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    // { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    // { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  ],

  /* Run your local dev server before starting the tests */
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        command: 'npm start',
        url: 'http://localhost:3000',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
      },
});
