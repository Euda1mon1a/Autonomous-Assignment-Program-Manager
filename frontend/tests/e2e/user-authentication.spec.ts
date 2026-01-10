/**
 * E2E tests for user authentication.
 *
 * Tests login, logout, and session management.
 */

import { test, expect } from '@playwright/test';

test.describe('User Authentication', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="username"]', 'testadmin');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="username"]', 'invalid');
    await page.fill('[name="password"]', 'wrongpass');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[name="username"]', 'testadmin');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');

    // Click logout
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should remember me option', async ({ page, context }) => {
    await page.goto('/login');

    await page.fill('[name="username"]', 'testadmin');
    await page.fill('[name="password"]', 'testpass123');
    await page.check('[name="remember"]');
    await page.click('button[type="submit"]');

    // Close page and open new one
    await page.close();
    const newPage = await context.newPage();
    await newPage.goto('/dashboard');

    // Should still be logged in
    await expect(newPage).toHaveURL(/\/dashboard/);
  });

  test('should change password', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="username"]', 'testadmin');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');

    await page.goto('/settings/password');

    await page.fill('[name="old_password"]', 'testpass123');
    await page.fill('[name="newPassword"]', 'newpass123');
    await page.fill('[name="confirmPassword"]', 'newpass123');
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });
});
