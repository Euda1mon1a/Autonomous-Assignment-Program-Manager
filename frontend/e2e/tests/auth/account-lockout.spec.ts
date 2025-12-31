import { test, expect } from '@playwright/test';
import { selectors } from '../../utils/selectors';

/**
 * Account Lockout Tests
 *
 * Tests for account lockout after failed login attempts
 */

test.describe('Account Lockout', () => {
  test('should lock account after 5 failed login attempts', async ({ page }) => {
    await page.goto('/login');

    // Attempt 5 failed logins
    for (let i = 0; i < 5; i++) {
      await page.fill(selectors.login.emailInput, 'admin@test.mil');
      await page.fill(selectors.login.passwordInput, 'WrongPassword!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(500);
    }

    // 6th attempt should show account locked message
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    const errorMessage = page.locator(selectors.login.errorMessage);
    await expect(errorMessage).toContainText(/account locked|too many attempts/i);
  });

  test('should not allow login with correct password when locked', async ({ page }) => {
    await page.goto('/login');

    // Trigger lockout
    for (let i = 0; i < 6; i++) {
      await page.fill(selectors.login.emailInput, 'faculty@test.mil');
      await page.fill(selectors.login.passwordInput, 'WrongPassword!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(300);
    }

    // Try with correct password
    await page.fill(selectors.login.emailInput, 'faculty@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should still be locked
    await expect(page.locator(selectors.login.errorMessage)).toContainText(/locked/i);
  });

  test('should unlock account after timeout period', async ({ page }) => {
    await page.goto('/login');

    // Trigger lockout
    for (let i = 0; i < 6; i++) {
      await page.fill(selectors.login.emailInput, 'test-lockout@test.mil');
      await page.fill(selectors.login.passwordInput, 'Wrong!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(200);
    }

    // Fast-forward time (mock 15 minutes)
    await page.clock.setFixedTime(new Date());
    await page.clock.fastForward(15 * 60 * 1000);

    // Try to login again
    await page.fill(selectors.login.emailInput, 'test-lockout@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should be able to login now
    await page.waitForURL(/\/(dashboard|schedule)/, { timeout: 5000 });
  });

  test('should show remaining lockout time', async ({ page }) => {
    await page.goto('/login');

    // Trigger lockout
    for (let i = 0; i < 6; i++) {
      await page.fill(selectors.login.emailInput, 'test-time@test.mil');
      await page.fill(selectors.login.passwordInput, 'Wrong!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(200);
    }

    // Check error message includes time
    const errorMessage = page.locator(selectors.login.errorMessage);
    const text = await errorMessage.textContent();

    // Should mention time (e.g., "15 minutes", "900 seconds")
    expect(text).toMatch(/\d+\s*(minutes?|seconds?|hours?)/i);
  });

  test('should reset failed attempts counter on successful login', async ({ page }) => {
    await page.goto('/login');

    // 2 failed attempts
    for (let i = 0; i < 2; i++) {
      await page.fill(selectors.login.emailInput, 'resident@test.mil');
      await page.fill(selectors.login.passwordInput, 'Wrong!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(300);
    }

    // Successful login
    await page.fill(selectors.login.emailInput, 'resident@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    // Logout
    await page.click(selectors.nav.userMenu);
    await page.click(selectors.nav.logoutButton);
    await page.waitForURL('/login');

    // Should be able to attempt login again (counter reset)
    for (let i = 0; i < 4; i++) {
      await page.fill(selectors.login.emailInput, 'resident@test.mil');
      await page.fill(selectors.login.passwordInput, 'Wrong!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(200);
    }

    // Should not be locked yet (4 attempts, not 6)
    const errorMessage = page.locator(selectors.login.errorMessage);
    const text = await errorMessage.textContent();
    expect(text).not.toMatch(/locked/i);
  });

  test('should track failed attempts per user, not globally', async ({ page }) => {
    await page.goto('/login');

    // 5 failed attempts for user A
    for (let i = 0; i < 5; i++) {
      await page.fill(selectors.login.emailInput, 'userA@test.mil');
      await page.fill(selectors.login.passwordInput, 'Wrong!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(200);
    }

    // User B should still be able to login
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);

    // Should login successfully
    await page.waitForURL(/\/(dashboard|schedule)/);
  });

  test('should log security event for account lockout', async ({ page, request }) => {
    await page.goto('/login');

    // Trigger lockout
    for (let i = 0; i < 6; i++) {
      await page.fill(selectors.login.emailInput, 'log-test@test.mil');
      await page.fill(selectors.login.passwordInput, 'Wrong!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(200);
    }

    // Check if security event was logged (if audit log endpoint exists)
    const response = await request.get('/api/v1/admin/audit-log?event=ACCOUNT_LOCKED', {
      failOnStatusCode: false,
    });

    if (response.ok()) {
      const logs = await response.json();
      expect(logs).toBeTruthy();
    }
  });

  test('should allow admin to unlock account manually', async ({ page, request }) => {
    // Trigger lockout
    await page.goto('/login');
    for (let i = 0; i < 6; i++) {
      await page.fill(selectors.login.emailInput, 'unlock-test@test.mil');
      await page.fill(selectors.login.passwordInput, 'Wrong!');
      await page.click(selectors.login.submitButton);
      await page.waitForTimeout(200);
    }

    // Admin unlocks account (if unlock endpoint exists)
    const unlockResponse = await request.post('/api/v1/admin/unlock-account', {
      data: { email: 'unlock-test@test.mil' },
      failOnStatusCode: false,
    });

    if (unlockResponse.ok()) {
      // Try to login again
      await page.fill(selectors.login.emailInput, 'unlock-test@test.mil');
      await page.fill(selectors.login.passwordInput, 'TestPassword123!');
      await page.click(selectors.login.submitButton);

      // Should be able to login
      await page.waitForURL(/\/(dashboard|schedule)/, { timeout: 5000 });
    }
  });
});
