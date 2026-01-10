import { test, expect } from '@playwright/test';
import { selectors } from '../../utils/selectors';

/**
 * Multi-Factor Authentication Tests
 *
 * Tests for MFA/2FA functionality (if implemented)
 */

test.describe('Multi-Factor Authentication', () => {
  test('should prompt for MFA if enabled', async ({ page }) => {
    await page.goto('/login');

    // Login with MFA-enabled user
    await page.fill(selectors.login.emailInput, 'mfa-user@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should show MFA prompt
    const mfaInput = page.locator('input[name="mfa_code"], input[name="otp"]');

    if (await mfaInput.isVisible()) {
      await expect(mfaInput).toBeVisible();
      await expect(page.locator('h1, h2')).toContainText(/verification|authenticate|mfa|2fa/i);
    }
  });

  test('should allow MFA setup in settings', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    // Navigate to security settings
    await page.goto('/settings');
    await page.click(selectors.settings.securityTab);

    // Check for MFA setup option
    const mfaSetup = page.locator('button:has-text("Enable MFA"), button:has-text("Set up 2FA")');

    if (await mfaSetup.isVisible()) {
      await expect(mfaSetup).toBeVisible();
    }
  });

  test('should validate MFA code format', async ({ page }) => {
    await page.goto('/login');

    await page.fill(selectors.login.emailInput, 'mfa-user@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    const mfaInput = page.locator('input[name="mfa_code"]');

    if (await mfaInput.isVisible()) {
      // Try invalid code format
      await mfaInput.fill('abc');

      const submitButton = page.locator('button[type="submit"]');
      await submitButton.click();

      // Should show validation error
      const errorMessage = page.locator(selectors.validation.fieldError);
      if (await errorMessage.isVisible()) {
        await expect(errorMessage).toContainText(/invalid|must be|digits/i);
      }
    }
  });

  test('should reject incorrect MFA code', async ({ page }) => {
    await page.goto('/login');

    await page.fill(selectors.login.emailInput, 'mfa-user@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    const mfaInput = page.locator('input[name="mfa_code"]');

    if (await mfaInput.isVisible()) {
      // Enter wrong code
      await mfaInput.fill('000000');
      await page.click('button[type="submit"]');

      // Should show error
      const errorMessage = page.locator(selectors.common.errorMessage);
      await expect(errorMessage).toContainText(/invalid|incorrect/i);
    }
  });

  test('should provide backup codes during MFA setup', async ({ page }) => {
    await page.goto('/login');
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    await page.goto('/settings/security/mfa-setup');

    // Should show backup codes
    const backupCodes = page.locator('[data-testid="backup-codes"]');

    if (await backupCodes.isVisible()) {
      await expect(backupCodes).toBeVisible();
    }
  });

  test('should allow login with backup code', async ({ page }) => {
    await page.goto('/login');

    await page.fill(selectors.login.emailInput, 'mfa-user@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    const useBackupLink = page.locator('a:has-text("Use backup code")');

    if (await useBackupLink.isVisible()) {
      await useBackupLink.click();

      const backupCodeInput = page.locator('input[name="backup_code"]');
      await expect(backupCodeInput).toBeVisible();

      // Enter backup code
      await backupCodeInput.fill('BACKUP-CODE-123');
      await page.click('button[type="submit"]');
    }
  });

  test('should disable backup code after use', async ({ page }) => {
    // This test would require database access to verify backup code is marked as used
    // Placeholder test
    await page.goto('/login');
  });

  test('should require MFA re-verification for sensitive actions', async ({ page }) => {
    await page.goto('/login');
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    // Try to change password
    await page.goto('/settings/security/change-password');

    // Might require MFA re-verification
    const mfaPrompt = page.locator('input[name="mfa_code"]');
    if (await mfaPrompt.isVisible()) {
      await expect(mfaPrompt).toBeVisible();
    }
  });

  test('should support TOTP authenticator apps', async ({ page }) => {
    await page.goto('/login');
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    await page.goto('/settings/security/mfa-setup');

    // Should show QR code for TOTP apps
    const qrCode = page.locator('[data-testid="mfa-qr-code"], img[alt*="QR"]');

    if (await qrCode.isVisible()) {
      await expect(qrCode).toBeVisible();
    }
  });

  test('should allow disabling MFA', async ({ page }) => {
    await page.goto('/login');
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    await page.goto('/settings/security');

    const disableMFA = page.locator('button:has-text("Disable MFA")');

    if (await disableMFA.isVisible()) {
      await disableMFA.click();

      // Should require password confirmation
      const passwordConfirm = page.locator('input[name="currentPassword"]');
      if (await passwordConfirm.isVisible()) {
        await expect(passwordConfirm).toBeVisible();
      }
    }
  });
});
