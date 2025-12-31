import { test, expect } from '@playwright/test';
import { selectors } from '../../utils/selectors';
import { waitForToast, waitForNetworkIdle } from '../../utils/test-helpers';

/**
 * Login Flow Tests
 *
 * Tests for user login functionality including:
 * - Successful login
 * - Invalid credentials
 * - Form validation
 * - Remember me functionality
 * - Rate limiting
 */

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    // Verify page title
    await expect(page).toHaveTitle(/Login/);

    // Verify form elements present
    await expect(page.locator(selectors.login.emailInput)).toBeVisible();
    await expect(page.locator(selectors.login.passwordInput)).toBeVisible();
    await expect(page.locator(selectors.login.submitButton)).toBeVisible();
    await expect(page.locator(selectors.login.forgotPasswordLink)).toBeVisible();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    // Fill login form
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Wait for navigation
    await page.waitForURL(/\/(dashboard|schedule)/);

    // Verify user is logged in
    await expect(page.locator(selectors.nav.userMenu)).toBeVisible();

    // Verify on dashboard
    await expect(page.locator(selectors.dashboard.welcomeMessage)).toBeVisible();
  });

  test('should show error with invalid email', async ({ page }) => {
    // Fill with invalid email
    await page.fill(selectors.login.emailInput, 'invalid-email');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should show validation error (client-side)
    const emailInput = page.locator(selectors.login.emailInput);
    await expect(emailInput).toHaveAttribute('aria-invalid', 'true');
  });

  test('should show error with incorrect password', async ({ page }) => {
    // Fill with wrong password
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'WrongPassword123!');
    await page.click(selectors.login.submitButton);

    // Wait for error message
    await expect(page.locator(selectors.login.errorMessage)).toBeVisible();
    await expect(page.locator(selectors.login.errorMessage)).toContainText(/Invalid credentials/i);

    // Should still be on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('should show error with non-existent user', async ({ page }) => {
    // Fill with non-existent email
    await page.fill(selectors.login.emailInput, 'nonexistent@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Wait for error message
    await expect(page.locator(selectors.login.errorMessage)).toBeVisible();
    await expect(page.locator(selectors.login.errorMessage)).toContainText(/Invalid credentials/i);
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit without filling fields
    await page.click(selectors.login.submitButton);

    // Email should be required
    const emailInput = page.locator(selectors.login.emailInput);
    await expect(emailInput).toHaveAttribute('required');

    // Password should be required
    const passwordInput = page.locator(selectors.login.passwordInput);
    await expect(passwordInput).toHaveAttribute('required');
  });

  test('should toggle password visibility', async ({ page }) => {
    // Fill password
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');

    // Password should be hidden
    await expect(page.locator(selectors.login.passwordInput)).toHaveAttribute('type', 'password');

    // Click toggle button (if exists)
    const toggleButton = page.locator('[data-testid="toggle-password"]');
    if (await toggleButton.isVisible()) {
      await toggleButton.click();

      // Password should be visible
      await expect(page.locator(selectors.login.passwordInput)).toHaveAttribute('type', 'text');

      // Click again to hide
      await toggleButton.click();
      await expect(page.locator(selectors.login.passwordInput)).toHaveAttribute('type', 'password');
    }
  });

  test('should handle remember me checkbox', async ({ page }) => {
    const rememberCheckbox = page.locator(selectors.login.rememberMeCheckbox);

    if (await rememberCheckbox.isVisible()) {
      // Check remember me
      await rememberCheckbox.check();
      await expect(rememberCheckbox).toBeChecked();

      // Login
      await page.fill(selectors.login.emailInput, 'admin@test.mil');
      await page.fill(selectors.login.passwordInput, 'TestPassword123!');
      await page.click(selectors.login.submitButton);

      await page.waitForURL(/\/(dashboard|schedule)/);

      // Verify session persists (check cookies)
      const cookies = await page.context().cookies();
      const sessionCookie = cookies.find((c) => c.name === 'session' || c.name === 'access_token');
      expect(sessionCookie).toBeDefined();
    }
  });

  test('should focus first input on load', async ({ page }) => {
    // Email input should have focus
    const emailInput = page.locator(selectors.login.emailInput);
    await expect(emailInput).toBeFocused();
  });

  test('should submit form with Enter key', async ({ page }) => {
    // Fill form
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');

    // Press Enter
    await page.keyboard.press('Enter');

    // Should navigate to dashboard
    await page.waitForURL(/\/(dashboard|schedule)/);
  });

  test('should redirect to intended page after login', async ({ page }) => {
    // Try to access protected page while logged out
    await page.goto('/schedule');

    // Should redirect to login with return URL
    await page.waitForURL(/\/login\?.*returnUrl=/);

    // Login
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should redirect back to schedule page
    await page.waitForURL('/schedule');
  });

  test('should prevent access to login page when already logged in', async ({ page }) => {
    // Login first
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    // Try to access login page
    await page.goto('/login');

    // Should redirect to dashboard
    await page.waitForURL(/\/(dashboard|schedule)/);
  });

  test('should handle rate limiting gracefully', async ({ page }) => {
    // Attempt multiple failed logins
    for (let i = 0; i < 5; i++) {
      await page.fill(selectors.login.emailInput, 'admin@test.mil');
      await page.fill(selectors.login.passwordInput, 'WrongPassword!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(500);
    }

    // Next attempt should show rate limit error
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should show rate limit message
    const errorMessage = page.locator(selectors.login.errorMessage);
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toContainText(/too many attempts|rate limit/i);
    }
  });

  test('should clear error message on input change', async ({ page }) => {
    // Trigger error
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'WrongPassword!');
    await page.click(selectors.login.submitButton);

    await expect(page.locator(selectors.login.errorMessage)).toBeVisible();

    // Change input
    await page.fill(selectors.login.passwordInput, 'NewPassword!');

    // Error should clear
    await expect(page.locator(selectors.login.errorMessage)).not.toBeVisible();
  });

  test('should be accessible with keyboard navigation', async ({ page }) => {
    // Tab through form
    await page.keyboard.press('Tab'); // Email
    await expect(page.locator(selectors.login.emailInput)).toBeFocused();

    await page.keyboard.press('Tab'); // Password
    await expect(page.locator(selectors.login.passwordInput)).toBeFocused();

    await page.keyboard.press('Tab'); // Submit button
    await expect(page.locator(selectors.login.submitButton)).toBeFocused();

    // Can activate with Space or Enter
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.locator(selectors.login.submitButton).focus();
    await page.keyboard.press('Space');

    await page.waitForURL(/\/(dashboard|schedule)/);
  });
});

test.describe('Login Page - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

  test('should be responsive on mobile', async ({ page }) => {
    await page.goto('/login');

    // Form should be visible and usable
    await expect(page.locator(selectors.login.emailInput)).toBeVisible();
    await expect(page.locator(selectors.login.passwordInput)).toBeVisible();
    await expect(page.locator(selectors.login.submitButton)).toBeVisible();

    // Login should work
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    await page.waitForURL(/\/(dashboard|schedule)/);
  });
});
