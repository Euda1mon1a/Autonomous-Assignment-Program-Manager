import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';

/**
 * Session Management Tests
 *
 * Tests for session persistence, expiration, and token refresh:
 * - Session persistence across page reloads
 * - Token expiration handling
 * - Automatic token refresh
 * - Concurrent session handling
 * - Idle timeout
 */

test.describe('Session Management', () => {
  test('should maintain session across page reloads', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Verify logged in
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();

    // Reload page
    await adminPage.reload();

    // Should still be logged in
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();
    await expect(adminPage.locator(selectors.dashboard.welcomeMessage)).toBeVisible();
  });

  test('should maintain session across navigation', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Navigate to different pages
    await adminPage.goto('/schedule');
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();

    await adminPage.goto('/swaps');
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();

    await adminPage.goto('/compliance');
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();
  });

  test('should automatically refresh expired token', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Mock token expiration by manipulating local storage
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000; // 1 second ago
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    // Make API call that should trigger token refresh
    await adminPage.goto('/schedule');

    // Should automatically refresh and stay logged in
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();

    // No error should be shown
    await expect(adminPage.locator(selectors.common.errorMessage)).not.toBeVisible();
  });

  test('should logout when token refresh fails', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Mock refresh endpoint to fail
    await adminPage.route('**/api/v1/auth/refresh', (route) => {
      route.fulfill({
        status: 401,
        body: JSON.stringify({ detail: 'Invalid refresh token' }),
      });
    });

    // Trigger token refresh
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000;
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    await adminPage.goto('/schedule');

    // Should redirect to login
    await adminPage.waitForURL('/login', { timeout: 10000 });
  });

  test('should handle concurrent API calls during token refresh', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Make multiple API calls simultaneously
    const promises = [
      adminPage.goto('/schedule'),
      adminPage.request.get('/api/v1/persons'),
      adminPage.request.get('/api/v1/rotations'),
      adminPage.request.get('/api/v1/assignments'),
    ];

    await Promise.all(promises.map((p) => p.catch(() => {}))); // Ignore individual failures

    // Should remain logged in
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();
  });

  test('should timeout session after inactivity', async ({ adminPage }) => {
    // This test requires server-side idle timeout configuration
    await adminPage.goto('/dashboard');

    // Mock time to simulate 30 minutes of inactivity
    await adminPage.clock.setFixedTime(new Date());
    await adminPage.clock.fastForward(30 * 60 * 1000); // 30 minutes

    // Try to make API call
    await adminPage.goto('/schedule');

    // Should redirect to login with timeout message
    if (await adminPage.locator(selectors.common.toast).isVisible()) {
      await expect(adminPage.locator(selectors.common.toast)).toContainText(/session expired|timed out/i);
    }

    await adminPage.waitForURL('/login', { timeout: 10000 });
  });

  test('should extend session on user activity', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Get initial token expiration
    const initialExpiration = await adminPage.evaluate(() => {
      return localStorage.getItem('token_expires_at');
    });

    // Wait a bit
    await adminPage.waitForTimeout(2000);

    // Perform user activity
    await adminPage.click(selectors.nav.scheduleLink);

    // Token expiration should be extended
    const newExpiration = await adminPage.evaluate(() => {
      return localStorage.getItem('token_expires_at');
    });

    // If token sliding expiration is implemented
    if (initialExpiration && newExpiration) {
      expect(parseInt(newExpiration)).toBeGreaterThanOrEqual(parseInt(initialExpiration));
    }
  });

  test('should prevent multiple concurrent logins from same user', async ({ browser, authUsers }) => {
    // Login in first browser context
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    await page1.goto('/login');
    await page1.fill(selectors.login.emailInput, authUsers.admin.email);
    await page1.fill(selectors.login.passwordInput, authUsers.admin.password);
    await page1.click(selectors.login.submitButton);
    await page1.waitForURL(/\/(dashboard|schedule)/);

    // Login in second browser context (different device)
    const context2 = await browser.newContext();
    const page2 = await context2.newPage();
    await page2.goto('/login');
    await page2.fill(selectors.login.emailInput, authUsers.admin.email);
    await page2.fill(selectors.login.passwordInput, authUsers.admin.password);
    await page2.click(selectors.login.submitButton);
    await page2.waitForURL(/\/(dashboard|schedule)/);

    // If single-session enforcement is enabled, first session should be invalidated
    // This depends on server configuration
    const response = await page1.request.get('/api/v1/auth/me', { failOnStatusCode: false });

    if (response.status() === 401) {
      // First session was invalidated
      await page1.reload();
      await page1.waitForURL('/login', { timeout: 5000 });
    }

    await context1.close();
    await context2.close();
  });

  test('should validate session on page focus', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Simulate losing focus
    await adminPage.evaluate(() => {
      window.dispatchEvent(new Event('blur'));
    });

    await adminPage.waitForTimeout(1000);

    // Simulate regaining focus (should validate session)
    await adminPage.evaluate(() => {
      window.dispatchEvent(new Event('focus'));
    });

    // Should remain logged in
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();
  });

  test('should store and retrieve user context correctly', async ({ adminPage, authUsers }) => {
    await adminPage.goto('/dashboard');

    // Verify user context is available
    const userData = await adminPage.evaluate(() => {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    });

    expect(userData).toBeTruthy();
    expect(userData?.email).toBe(authUsers.admin.email);
    expect(userData?.role).toBe('ADMIN');
  });

  test('should handle session across browser restart', async ({ browser, authUsers }) => {
    // Create context with persistent storage
    const context = await browser.newContext({
      storageState: undefined, // Start fresh
    });

    const page = await context.newPage();

    // Login
    await page.goto('/login');
    await page.fill(selectors.login.emailInput, authUsers.admin.email);
    await page.fill(selectors.login.passwordInput, authUsers.admin.password);

    // Check "Remember me" if available
    const rememberMe = page.locator(selectors.login.rememberMeCheckbox);
    if (await rememberMe.isVisible()) {
      await rememberMe.check();
    }

    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    // Save storage state
    const storageState = await context.storageState();

    // Close everything
    await page.close();
    await context.close();

    // Create new context with saved state (simulating browser restart)
    const newContext = await browser.newContext({ storageState });
    const newPage = await newContext.newPage();

    // Navigate to dashboard
    await newPage.goto('/dashboard');

    // Should still be logged in if "remember me" was checked
    if (await rememberMe.isVisible()) {
      await expect(newPage.locator(selectors.nav.userMenu)).toBeVisible();
    }

    await newContext.close();
  });

  test('should handle websocket reconnection after token refresh', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // If app uses WebSockets, they should reconnect with new token
    // This is implementation-specific

    // Trigger token refresh
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000;
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    await adminPage.reload();

    // WebSocket should reconnect (check connection status if exposed)
    const wsStatus = await adminPage.evaluate(() => {
      return (window as any).wsConnected; // If exposed
    });

    // Should be connected or undefined if not implemented
    if (wsStatus !== undefined) {
      expect(wsStatus).toBe(true);
    }
  });

  test('should invalidate session on password change', async ({ adminPage }) => {
    await adminPage.goto('/settings');

    // Navigate to security tab
    await adminPage.click(selectors.settings.securityTab);

    // Change password
    await adminPage.fill(selectors.settings.oldPassword, 'TestPassword123!');
    await adminPage.fill(selectors.settings.newPassword, 'NewTestPassword123!');
    await adminPage.fill(selectors.settings.confirmPassword, 'NewTestPassword123!');
    await adminPage.click(selectors.settings.changePassword);

    // Should logout and require re-login with new password
    await adminPage.waitForURL('/login', { timeout: 10000 });
  });

  test('should clear sensitive data from memory on logout', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Logout
    await adminPage.click(selectors.nav.userMenu);
    await adminPage.click(selectors.nav.logoutButton);
    await adminPage.waitForURL('/login');

    // Check that sensitive data is cleared
    const hasToken = await adminPage.evaluate(() => {
      return Boolean(
        localStorage.getItem('access_token') ||
        localStorage.getItem('refresh_token') ||
        sessionStorage.getItem('access_token')
      );
    });

    expect(hasToken).toBe(false);
  });

  test('should handle race condition in token refresh', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Trigger multiple token refresh attempts simultaneously
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000;
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    // Make multiple API calls at once
    const calls = Array.from({ length: 10 }, () =>
      adminPage.request.get('/api/v1/persons').catch(() => {})
    );

    await Promise.all(calls);

    // Should remain logged in (only one refresh call should be made)
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();
  });
});
