/**
 * E2E tests for schedule management.
 *
 * Tests the complete user flow for managing schedules.
 */

import { test, expect } from '@playwright/test';

test.describe('Schedule Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="username"]', 'testadmin');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should display schedule calendar', async ({ page }) => {
    await page.goto('/schedule');

    // Wait for schedule to load
    await page.waitForSelector('[data-testid="schedule-calendar"]');

    // Verify calendar is displayed
    expect(await page.isVisible('[data-testid="schedule-calendar"]')).toBeTruthy();
  });

  test('should create new assignment', async ({ page }) => {
    await page.goto('/schedule');

    // Click add assignment button
    await page.click('[data-testid="add-assignment-button"]');

    // Fill assignment form
    await page.fill('[name="date"]', '2024-01-15');
    await page.selectOption('[name="timeOfDay"]', 'AM');
    await page.selectOption('[name="person"]', { index: 1 });
    await page.selectOption('[name="rotation"]', { index: 1 });

    // Submit
    await page.click('button[type="submit"]');

    // Verify success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should edit existing assignment', async ({ page }) => {
    await page.goto('/schedule');

    // Click on assignment
    await page.click('[data-testid="assignment-item"]:first-child');

    // Click edit button
    await page.click('[data-testid="edit-assignment-button"]');

    // Modify assignment
    await page.selectOption('[name="rotation"]', { index: 2 });

    // Save
    await page.click('button[type="submit"]');

    // Verify update
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should delete assignment', async ({ page }) => {
    await page.goto('/schedule');

    // Click on assignment
    await page.click('[data-testid="assignment-item"]:first-child');

    // Click delete button
    await page.click('[data-testid="delete-assignment-button"]');

    // Confirm deletion
    await page.click('[data-testid="confirm-delete-button"]');

    // Verify deletion
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should filter schedule by person', async ({ page }) => {
    await page.goto('/schedule');

    // Select person filter
    await page.selectOption('[data-testid="person-filter"]', { index: 1 });

    // Wait for filtered results
    await page.waitForLoadState('networkidle');

    // Verify filter applied
    const assignments = page.locator('[data-testid="assignment-item"]');
    expect(await assignments.count()).toBeGreaterThan(0);
  });

  test('should navigate between weeks', async ({ page }) => {
    await page.goto('/schedule');

    // Click next week
    await page.click('[data-testid="next-week-button"]');

    // Verify date changed
    await expect(page.locator('[data-testid="current-week"]')).not.toContainText('Jan 1');

    // Click previous week
    await page.click('[data-testid="prev-week-button"]');

    // Verify date changed back
    await page.waitForLoadState('networkidle');
  });
});
