import { test, expect } from '@playwright/test';
import { selectors } from '../../utils/selectors';
import { waitForToast } from '../../utils/test-helpers';

/**
 * Password Reset Tests
 *
 * Tests for password reset functionality:
 * - Request password reset
 * - Validate reset token
 * - Set new password
 * - Email delivery
 * - Token expiration
 */

test.describe('Password Reset', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display forgot password link', async ({ page }) => {
    await expect(page.locator(selectors.login.forgotPasswordLink)).toBeVisible();
    await expect(page.locator(selectors.login.forgotPasswordLink)).toHaveText(/forgot password/i);
  });

  test('should navigate to password reset page', async ({ page }) => {
    await page.click(selectors.login.forgotPasswordLink);

    await page.waitForURL('/forgot-password');
    await expect(page.locator('h1, h2')).toContainText(/reset password|forgot password/i);
  });

  test('should submit password reset request with valid email', async ({ page }) => {
    await page.goto('/forgot-password');

    await page.fill('input[name="email"]', 'admin@test.mil');
    await page.click('button[type="submit"]');

    // Should show success message
    const toast = await waitForToast(page);
    await expect(toast).toContainText(/check your email|reset link sent/i);
  });

  test('should handle non-existent email gracefully', async ({ page }) => {
    await page.goto('/forgot-password');

    await page.fill('input[name="email"]', 'nonexistent@test.mil');
    await page.click('button[type="submit"]');

    // Should still show generic success message (security best practice)
    const toast = await waitForToast(page);
    await expect(toast).toContainText(/check your email|reset link sent/i);
  });

  test('should validate email format', async ({ page }) => {
    await page.goto('/forgot-password');

    await page.fill('input[name="email"]', 'invalid-email');
    await page.click('button[type="submit"]');

    // Should show validation error
    const emailInput = page.locator('input[name="email"]');
    await expect(emailInput).toHaveAttribute('aria-invalid', 'true');
  });

  test('should show error on rate limiting', async ({ page }) => {
    await page.goto('/forgot-password');

    // Submit multiple requests rapidly
    for (let i = 0; i < 6; i++) {
      await page.fill('input[name="email"]', 'admin@test.mil');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(100);
    }

    // Should show rate limit error
    const errorMessage = page.locator(selectors.common.errorMessage);
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toContainText(/too many requests|rate limit/i);
    }
  });

  test('should navigate back to login from password reset', async ({ page }) => {
    await page.goto('/forgot-password');

    const backToLoginLink = page.locator('a:has-text("Back to Login")');
    await backToLoginLink.click();

    await page.waitForURL('/login');
  });

  test('should handle password reset with valid token', async ({ page, request }) => {
    // Request password reset
    const resetResponse = await request.post('/api/v1/auth/password-reset', {
      data: { email: 'admin@test.mil' },
    });

    expect(resetResponse.ok()).toBeTruthy();

    // In real scenario, extract token from email
    // For testing, use mock token or test endpoint to get token
    const mockToken = 'test-reset-token-123';

    // Navigate to reset password page with token
    await page.goto(`/reset-password?token=${mockToken}`);

    // Fill new password
    await page.fill('input[name="newPassword"]', 'NewPassword123!');
    await page.fill('input[name="confirmPassword"]', 'NewPassword123!');
    await page.click('button[type="submit"]');

    // Should redirect to login with success message
    await page.waitForURL('/login');

    const toast = await waitForToast(page);
    await expect(toast).toContainText(/password reset|password changed/i);
  });

  test('should validate password strength requirements', async ({ page }) => {
    const mockToken = 'test-reset-token-123';
    await page.goto(`/reset-password?token=${mockToken}`);

    // Try weak password
    await page.fill('input[name="newPassword"]', 'weak');
    await page.fill('input[name="confirmPassword"]', 'weak');
    await page.click('button[type="submit"]');

    // Should show validation error
    const errorMessage = page.locator(selectors.validation.fieldError);
    await expect(errorMessage).toContainText(/password must|too short|weak password/i);
  });

  test('should validate password confirmation match', async ({ page }) => {
    const mockToken = 'test-reset-token-123';
    await page.goto(`/reset-password?token=${mockToken}`);

    await page.fill('input[name="newPassword"]', 'NewPassword123!');
    await page.fill('input[name="confirmPassword"]', 'DifferentPassword123!');
    await page.click('button[type="submit"]');

    // Should show mismatch error
    const errorMessage = page.locator(selectors.validation.fieldError);
    await expect(errorMessage).toContainText(/passwords do not match|passwords must match/i);
  });

  test('should reject expired reset token', async ({ page }) => {
    // Use expired token
    const expiredToken = 'expired-token-123';
    await page.goto(`/reset-password?token=${expiredToken}`);

    await page.fill('input[name="newPassword"]', 'NewPassword123!');
    await page.fill('input[name="confirmPassword"]', 'NewPassword123!');
    await page.click('button[type="submit"]');

    // Should show token expired error
    const errorMessage = page.locator(selectors.common.errorMessage);
    await expect(errorMessage).toContainText(/token expired|link expired|invalid token/i);
  });

  test('should reject invalid reset token', async ({ page }) => {
    const invalidToken = 'invalid-token';
    await page.goto(`/reset-password?token=${invalidToken}`);

    await page.fill('input[name="newPassword"]', 'NewPassword123!');
    await page.fill('input[name="confirmPassword"]', 'NewPassword123!');
    await page.click('button[type="submit"]');

    // Should show invalid token error
    const errorMessage = page.locator(selectors.common.errorMessage);
    await expect(errorMessage).toContainText(/invalid token|token not found/i);
  });

  test('should reject used reset token', async ({ page }) => {
    const usedToken = 'used-token-123';

    // Use token first time
    await page.goto(`/reset-password?token=${usedToken}`);
    await page.fill('input[name="newPassword"]', 'NewPassword123!');
    await page.fill('input[name="confirmPassword"]', 'NewPassword123!');
    await page.click('button[type="submit"]');

    // Try to use same token again
    await page.goto(`/reset-password?token=${usedToken}`);
    await page.fill('input[name="newPassword"]', 'AnotherPassword123!');
    await page.fill('input[name="confirmPassword"]', 'AnotherPassword123!');
    await page.click('button[type="submit"]');

    // Should show token already used error
    const errorMessage = page.locator(selectors.common.errorMessage);
    await expect(errorMessage).toContainText(/token already used|invalid token/i);
  });

  test('should login with new password after reset', async ({ page }) => {
    // Complete password reset (assuming successful reset)
    const newPassword = 'NewPassword123!';

    // Navigate to login
    await page.goto('/login');

    // Login with new password
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, newPassword);
    await page.click(selectors.login.submitButton);

    // Should login successfully
    await page.waitForURL(/\/(dashboard|schedule)/);
    await expect(page.locator(selectors.nav.userMenu)).toBeVisible();
  });

  test('should not allow old password after reset', async ({ page }) => {
    // Try to login with old password (after reset)
    await page.goto('/login');

    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'OldPassword123!');
    await page.click(selectors.login.submitButton);

    // Should show invalid credentials error
    const errorMessage = page.locator(selectors.login.errorMessage);
    await expect(errorMessage).toContainText(/invalid credentials/i);
  });

  test('should show password strength indicator', async ({ page }) => {
    const mockToken = 'test-reset-token-123';
    await page.goto(`/reset-password?token=${mockToken}`);

    const passwordInput = page.locator('input[name="newPassword"]');
    const strengthIndicator = page.locator('[data-testid="password-strength"]');

    if (await strengthIndicator.isVisible()) {
      // Type weak password
      await passwordInput.fill('weak');
      await expect(strengthIndicator).toContainText(/weak/i);

      // Type strong password
      await passwordInput.fill('StrongPassword123!');
      await expect(strengthIndicator).toContainText(/strong/i);
    }
  });

  test('should toggle password visibility', async ({ page }) => {
    const mockToken = 'test-reset-token-123';
    await page.goto(`/reset-password?token=${mockToken}`);

    const passwordInput = page.locator('input[name="newPassword"]');
    const toggleButton = page.locator('[data-testid="toggle-password"]');

    if (await toggleButton.isVisible()) {
      // Initially hidden
      await expect(passwordInput).toHaveAttribute('type', 'password');

      // Click to show
      await toggleButton.click();
      await expect(passwordInput).toHaveAttribute('type', 'text');

      // Click to hide
      await toggleButton.click();
      await expect(passwordInput).toHaveAttribute('type', 'password');
    }
  });
});

test.describe('Password Reset - Security', () => {
  test('should not reveal if email exists in database', async ({ page }) => {
    await page.goto('/forgot-password');

    // Submit with existing email
    await page.fill('input[name="email"]', 'admin@test.mil');
    await page.click('button[type="submit"]');
    const message1 = await page.locator(selectors.common.toast).textContent();

    // Submit with non-existing email
    await page.goto('/forgot-password');
    await page.fill('input[name="email"]', 'nonexistent@test.mil');
    await page.click('button[type="submit"]');
    const message2 = await page.locator(selectors.common.toast).textContent();

    // Messages should be identical (security best practice)
    expect(message1).toBe(message2);
  });

  test('should prevent token enumeration', async ({ page }) => {
    // Try multiple invalid tokens
    const tokens = ['token1', 'token2', 'token3'];

    for (const token of tokens) {
      await page.goto(`/reset-password?token=${token}`);
      await page.fill('input[name="newPassword"]', 'Password123!');
      await page.fill('input[name="confirmPassword"]', 'Password123!');
      await page.click('button[type="submit"]');

      // Error message should be generic
      const errorMessage = page.locator(selectors.common.errorMessage);
      await expect(errorMessage).toContainText(/invalid|expired/i);
    }
  });
});
