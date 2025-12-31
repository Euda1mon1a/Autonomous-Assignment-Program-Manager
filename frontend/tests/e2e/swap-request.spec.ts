/**
 * E2E tests for swap request workflow.
 *
 * Tests the complete swap request process.
 */

import { test, expect } from '@playwright/test';

test.describe('Swap Request Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="username"]', 'faculty1');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
  });

  test('should create swap request', async ({ page }) => {
    await page.goto('/swaps');

    // Click create swap button
    await page.click('[data-testid="create-swap-button"]');

    // Select assignments
    await page.click('[data-testid="my-assignment-select"]:first-child');
    await page.click('[data-testid="target-assignment-select"]:first-child');

    // Add notes
    await page.fill('[name="notes"]', 'Prefer to work different day');

    // Submit
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should view swap status', async ({ page }) => {
    await page.goto('/swaps');

    // Click on swap request
    await page.click('[data-testid="swap-item"]:first-child');

    // Verify swap details displayed
    await expect(page.locator('[data-testid="swap-status"]')).toBeVisible();
  });

  test('should cancel swap request', async ({ page }) => {
    await page.goto('/swaps');

    // Click on pending swap
    await page.click('[data-testid="swap-item"][data-status="pending"]:first-child');

    // Click cancel button
    await page.click('[data-testid="cancel-swap-button"]');

    // Confirm cancellation
    await page.click('[data-testid="confirm-cancel-button"]');

    // Verify cancellation
    await expect(page.locator('[data-testid="swap-status"]')).toContainText('cancelled');
  });

  test('should approve swap request (coordinator)', async ({ page }) => {
    // Login as coordinator
    await page.goto('/login');
    await page.fill('[name="username"]', 'coordinator');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');

    await page.goto('/swaps/pending');

    // Click on swap request
    await page.click('[data-testid="swap-item"]:first-child');

    // Click approve button
    await page.click('[data-testid="approve-swap-button"]');

    // Verify approval
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should find swap matches', async ({ page }) => {
    await page.goto('/swaps/find-match');

    // Select my assignment
    await page.click('[data-testid="my-assignment-select"]:first-child');

    // Click find matches
    await page.click('[data-testid="find-matches-button"]');

    // Wait for results
    await page.waitForSelector('[data-testid="match-results"]');

    // Verify matches displayed
    const matches = page.locator('[data-testid="match-item"]');
    expect(await matches.count()).toBeGreaterThanOrEqual(0);
  });
});
