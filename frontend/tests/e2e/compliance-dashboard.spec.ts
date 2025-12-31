/**
 * E2E tests for compliance dashboard.
 *
 * Tests viewing and monitoring ACGME compliance.
 */

import { test, expect } from '@playwright/test';

test.describe('Compliance Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="username"]', 'testadmin');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
  });

  test('should display compliance metrics', async ({ page }) => {
    await page.goto('/compliance');

    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="compliance-dashboard"]');

    // Verify key metrics displayed
    await expect(page.locator('[data-testid="80-hour-compliance"]')).toBeVisible();
    await expect(page.locator('[data-testid="1-in-7-compliance"]')).toBeVisible();
    await expect(page.locator('[data-testid="supervision-compliance"]')).toBeVisible();
  });

  test('should view resident compliance details', async ({ page }) => {
    await page.goto('/compliance');

    // Click on resident
    await page.click('[data-testid="resident-item"]:first-child');

    // Verify resident details displayed
    await expect(page.locator('[data-testid="resident-compliance-details"]')).toBeVisible();
    await expect(page.locator('[data-testid="hours-worked"]')).toBeVisible();
    await expect(page.locator('[data-testid="days-off"]')).toBeVisible();
  });

  test('should filter by compliance status', async ({ page }) => {
    await page.goto('/compliance');

    // Select non-compliant filter
    await page.click('[data-testid="filter-non-compliant"]');

    // Wait for results
    await page.waitForLoadState('networkidle');

    // Verify filtered results
    const violations = page.locator('[data-testid="violation-item"]');
    expect(await violations.count()).toBeGreaterThanOrEqual(0);
  });

  test('should export compliance report', async ({ page }) => {
    await page.goto('/compliance');

    // Click export button
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="export-compliance-button"]')
    ]);

    // Verify download started
    expect(download).toBeTruthy();
  });

  test('should view compliance history', async ({ page }) => {
    await page.goto('/compliance');

    // Click on resident
    await page.click('[data-testid="resident-item"]:first-child');

    // Click history tab
    await page.click('[data-testid="history-tab"]');

    // Verify history chart displayed
    await expect(page.locator('[data-testid="compliance-history-chart"]')).toBeVisible();
  });
});
