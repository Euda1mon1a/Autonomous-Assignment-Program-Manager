/**
 * E2E tests for settings management.
 *
 * Tests user preferences and system settings.
 */

import { test, expect } from '@playwright/test';

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="username"]', 'testadmin');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
  });

  test('should update profile information', async ({ page }) => {
    await page.goto('/settings/profile');

    // Update email
    await page.fill('[name="email"]', 'newemail@hospital.org');

    // Update phone
    await page.fill('[name="phone"]', '555-1234');

    // Save changes
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should update notification preferences', async ({ page }) => {
    await page.goto('/settings/notifications');

    // Enable email notifications
    await page.check('[name="email_enabled"]');

    // Disable SMS notifications
    await page.uncheck('[name="sms_enabled"]');

    // Select notification types
    await page.check('[name="schedule_changes"]');
    await page.check('[name="swap_requests"]');

    // Save
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should update display preferences', async ({ page }) => {
    await page.goto('/settings/display');

    // Select theme
    await page.click('[data-testid="theme-dark"]');

    // Set language
    await page.selectOption('[name="language"]', 'en');

    // Set timezone
    await page.selectOption('[name="timezone"]', 'America/New_York');

    // Save
    await page.click('button[type="submit"]');

    // Verify theme applied
    await expect(page.locator('html')).toHaveClass(/dark/);
  });

  test('should manage rotation templates (admin)', async ({ page }) => {
    await page.goto('/settings/rotations');

    // Click add rotation
    await page.click('[data-testid="add-rotation-button"]');

    // Fill form
    await page.fill('[name="name"]', 'New Rotation');
    await page.fill('[name="abbreviation"]', 'NR');
    await page.selectOption('[name="activity_type"]', 'outpatient');
    await page.fill('[name="max_residents"]', '4');

    // Save
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should configure ACGME rules (admin)', async ({ page }) => {
    await page.goto('/settings/acgme');

    // Update max hours
    await page.fill('[name="max_hours_per_week"]', '80');

    // Update max consecutive days
    await page.fill('[name="max_consecutive_days"]', '6');

    // Save
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should view system information', async ({ page }) => {
    await page.goto('/settings/system');

    // Verify system info displayed
    await expect(page.locator('[data-testid="version-info"]')).toBeVisible();
    await expect(page.locator('[data-testid="database-status"]')).toBeVisible();
  });
});
