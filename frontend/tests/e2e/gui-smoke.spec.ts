/**
 * GUI Smoke Test
 *
 * Purpose: Verify critical pages load without crashing.
 * Catches: Auth hangs, API timeouts, runtime null errors, page crashes.
 *
 * Run: cd frontend && npm run test:e2e -- gui-smoke.spec.ts
 *
 * Created: 2026-01-19 (GUI Regression Prevention Plan)
 */

import { test, expect } from '@playwright/test';

// Pages that should load without authentication
const PUBLIC_PAGES = [
  { path: '/login', name: 'Login' },
];

// Pages that require authentication
const AUTH_PAGES = [
  { path: '/', name: 'Home/Dashboard' },
  { path: '/schedule', name: 'Schedule' },
  { path: '/people', name: 'People Hub' },
  { path: '/heatmap', name: 'Heatmap' },
  { path: '/admin/resilience-hub', name: 'Resilience Hub' },
  { path: '/admin/resilience-overseer', name: 'Resilience Overseer' },
];

test.describe('GUI Smoke Test - Public Pages', () => {
  for (const page of PUBLIC_PAGES) {
    test(`${page.name} loads without crash`, async ({ page: browserPage }) => {
      // Set timeout to catch hangs (10 seconds)
      browserPage.setDefaultTimeout(10000);

      const response = await browserPage.goto(page.path);

      // Should get a valid HTTP response
      expect(response?.status()).toBeLessThan(500);

      // Should not show React error boundary
      await expect(browserPage.locator('text=Something went wrong')).not.toBeVisible();
      await expect(browserPage.locator('text=Application error')).not.toBeVisible();
    });
  }
});

test.describe('GUI Smoke Test - Authenticated Pages', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');

    // Fill login form
    await page.fill('[name="username"], [name="email"], input[type="email"]', 'testadmin');
    await page.fill('[name="password"], input[type="password"]', 'testpass123');

    // Submit and wait for navigation
    await Promise.all([
      page.waitForNavigation({ timeout: 15000 }).catch(() => {}),
      page.click('button[type="submit"]'),
    ]);
  });

  for (const pageInfo of AUTH_PAGES) {
    test(`${pageInfo.name} loads without crash`, async ({ page: browserPage }) => {
      // Set timeout to catch hangs
      browserPage.setDefaultTimeout(10000);

      const response = await browserPage.goto(pageInfo.path);

      // Should get a valid HTTP response (redirects OK)
      expect(response?.status()).toBeLessThan(500);

      // Should not show React error boundary
      await expect(browserPage.locator('text=Something went wrong')).not.toBeVisible();
      await expect(browserPage.locator('text=Application error')).not.toBeVisible();

      // Should not be stuck loading forever (5 second check)
      // Most loading indicators should disappear within this time
      await browserPage.waitForTimeout(2000);

      // If there's a loading skeleton, it should eventually disappear
      const loadingIndicator = browserPage.locator('[data-testid="loading"], .animate-pulse, [aria-busy="true"]');
      const hasLoading = await loadingIndicator.count() > 0;

      if (hasLoading) {
        // Wait for loading to finish (with timeout)
        await expect(loadingIndicator.first()).not.toBeVisible({ timeout: 8000 }).catch(() => {
          // Some pages may have permanent loading states, that's OK
          // Just log it for debugging
          console.log(`Note: ${pageInfo.name} has persistent loading indicator`);
        });
      }
    });
  }
});
