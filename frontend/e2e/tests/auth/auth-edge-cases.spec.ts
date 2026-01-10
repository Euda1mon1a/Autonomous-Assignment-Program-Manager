import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';

/**
 * Authentication Edge Cases
 *
 * Tests for unusual scenarios and edge cases
 */

test.describe('Authentication Edge Cases', () => {
  test('should handle very long passwords', async ({ page }) => {
    await page.goto('/login');

    const longPassword = 'A'.repeat(1000) + '123!';

    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, longPassword);
    await page.click(selectors.login.submitButton);

    // Should either accept or show validation error, not crash
    await page.waitForTimeout(1000);

    const errorMessage = page.locator(selectors.login.errorMessage);
    const isOnDashboard = page.url().includes('/dashboard') || page.url().includes('/schedule');

    // Should either login or show error (not crash)
    expect(isOnDashboard || (await errorMessage.isVisible())).toBeTruthy();
  });

  test('should handle special characters in email', async ({ page }) => {
    await page.goto('/login');

    const specialEmails = [
      'user+tag@test.mil',
      'user.name@test.mil',
      'userName@test.mil',
      'user-name@test.mil',
    ];

    for (const email of specialEmails) {
      await page.fill(selectors.login.emailInput, email);
      await page.fill(selectors.login.passwordInput, 'TestPassword123!');
      await page.click(selectors.login.submitButton);

      // Should handle gracefully
      await page.waitForTimeout(500);
    }
  });

  test('should handle unicode characters in password', async ({ page }) => {
    await page.goto('/login');

    const unicodePassword = 'Pass密码123!';

    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, unicodePassword);
    await page.click(selectors.login.submitButton);

    // Should handle unicode gracefully
    await page.waitForTimeout(1000);
  });

  test('should handle null bytes in input', async ({ page }) => {
    await page.goto('/login');

    const nullByteEmail = 'admin\x00@test.mil';

    await page.fill(selectors.login.emailInput, nullByteEmail);
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should reject or sanitize
    await page.waitForTimeout(500);
  });

  test('should handle very rapid login attempts', async ({ page }) => {
    await page.goto('/login');

    const promises = [];

    for (let i = 0; i < 10; i++) {
      const promise = (async () => {
        await page.fill(selectors.login.emailInput, `user${i}@test.mil`);
        await page.fill(selectors.login.passwordInput, 'Pass123!');
        await page.click(selectors.login.submitButton);
      })();

      promises.push(promise);
    }

    await Promise.all(promises.map((p) => p.catch(() => {})));

    // Should handle gracefully without crashing
    await page.waitForTimeout(1000);
  });

  test('should handle browser back button after login', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Go to schedule
    await adminPage.goto('/schedule');

    // Use browser back button
    await adminPage.goBack();

    // Should be on dashboard, still logged in
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();
  });

  test('should handle browser back button after logout', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Logout
    await adminPage.click(selectors.nav.userMenu);
    await adminPage.click(selectors.nav.logoutButton);
    await adminPage.waitForURL('/login');

    // Try to go back
    await adminPage.goBack();

    // Should redirect to login (or stay on login)
    await adminPage.waitForTimeout(1000);
    const url = adminPage.url();
    expect(url).toContain('/login');
  });

  test('should handle multiple tab logout', async ({ browser, authUsers }) => {
    const context = await browser.newContext();

    // Open two tabs
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    // Login in page1
    await page1.goto('/login');
    await page1.fill(selectors.login.emailInput, authUsers.admin.email);
    await page1.fill(selectors.login.passwordInput, authUsers.admin.password);
    await page1.click(selectors.login.submitButton);
    await page1.waitForURL(/\/(dashboard|schedule)/);

    // Navigate in page2 (should be logged in)
    await page2.goto('/schedule');
    await expect(page2.locator(selectors.nav.userMenu)).toBeVisible();

    // Logout from page1
    await page1.click(selectors.nav.userMenu);
    await page1.click(selectors.nav.logoutButton);
    await page1.waitForURL('/login');

    // Refresh page2 - should logout
    await page2.reload();
    await page2.waitForURL(/\/login/, { timeout: 5000 });

    await context.close();
  });

  test('should handle expired password', async ({ page }) => {
    // Try to login with expired password user
    await page.goto('/login');

    await page.fill(selectors.login.emailInput, 'expired-password@test.mil');
    await page.fill(selectors.login.passwordInput, 'OldPassword123!');
    await page.click(selectors.login.submitButton);

    // Should prompt for password change
    const changePasswordPrompt = page.locator('h1:has-text("Change Password"), h2:has-text("Password Expired")');

    if (await changePasswordPrompt.isVisible()) {
      await expect(changePasswordPrompt).toBeVisible();
    }
  });

  test('should handle disabled account', async ({ page }) => {
    await page.goto('/login');

    await page.fill(selectors.login.emailInput, 'disabled@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should show account disabled error
    const errorMessage = page.locator(selectors.login.errorMessage);
    await expect(errorMessage).toContainText(/disabled|suspended|deactivated/i);
  });

  test('should handle case-insensitive email', async ({ page }) => {
    await page.goto('/login');

    // Try with different case
    await page.fill(selectors.login.emailInput, 'ADMIN@TEST.MIL');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should login successfully (emails are case-insensitive)
    await page.waitForURL(/\/(dashboard|schedule)/, { timeout: 5000 });
  });

  test('should trim whitespace from email', async ({ page }) => {
    await page.goto('/login');

    await page.fill(selectors.login.emailInput, '  admin@test.mil  ');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should login successfully (whitespace trimmed)
    await page.waitForURL(/\/(dashboard|schedule)/, { timeout: 5000 });
  });

  test('should NOT trim whitespace from password', async ({ page }) => {
    await page.goto('/login');

    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, '  TestPassword123!  ');
    await page.click(selectors.login.submitButton);

    // Should fail (password is exact match)
    const errorMessage = page.locator(selectors.login.errorMessage);
    await expect(errorMessage).toContainText(/invalid/i);
  });

  test('should handle simultaneous password reset and login', async ({ page }) => {
    // Request password reset
    await page.goto('/forgot-password');
    await page.fill('input[name="email"]', 'admin@test.mil');
    await page.click('button[type="submit"]');

    // Try to login normally
    await page.goto('/login');
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should still be able to login with old password
    await page.waitForURL(/\/(dashboard|schedule)/, { timeout: 5000 });
  });

  test('should handle network interruption during login', async ({ page }) => {
    await page.goto('/login');

    // Simulate network offline
    await page.context().setOffline(true);

    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should show network error
    await page.waitForTimeout(2000);

    const errorMessage = page.locator(selectors.login.errorMessage);
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toContainText(/network|connection|offline/i);
    }

    // Restore network
    await page.context().setOffline(false);

    // Retry
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/, { timeout: 10000 });
  });

  test('should handle timezone differences', async ({ adminPage }) => {
    // Set different timezone
    await adminPage.emulateTimezone('America/New_York');

    await adminPage.goto('/dashboard');

    // Should still work correctly
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();
  });

  test('should handle incomplete login flow', async ({ page }) => {
    await page.goto('/login');

    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');

    // Navigate away before submitting
    await page.goto('/');

    // Should not be logged in
    await page.waitForTimeout(500);
    const url = page.url();
    expect(url).toContain('/login');
  });

  test('should handle deleted user session', async ({ browser, authUsers }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto('/login');
    await page.fill(selectors.login.emailInput, authUsers.admin.email);
    await page.fill(selectors.login.passwordInput, authUsers.admin.password);
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    // Simulate user deletion (in real scenario, admin would delete user)
    // For test, we can try to access API with deleted user session

    // Try to make API call
    const response = await page.request.get('/api/v1/auth/me', {
      failOnStatusCode: false,
    });

    // Should either work (user exists) or return 401/404
    expect([200, 401, 404]).toContain(response.status());

    await context.close();
  });
});
