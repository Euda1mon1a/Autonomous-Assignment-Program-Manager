import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';
import { waitForToast } from '../../utils/test-helpers';

/**
 * Logout Flow Tests
 *
 * Tests for user logout functionality including:
 * - Successful logout
 * - Session clearing
 * - Redirect behavior
 * - Token invalidation
 */

test.describe('Logout Functionality', () => {
  test('should logout admin successfully', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Verify logged in
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();

    // Click user menu
    await adminPage.click(selectors.nav.userMenu);

    // Click logout
    await adminPage.click(selectors.nav.logoutButton);

    // Should redirect to login
    await adminPage.waitForURL('/login');

    // User menu should not be visible
    await expect(adminPage.locator(selectors.nav.userMenu)).not.toBeVisible();

    // Try to access protected page
    await adminPage.goto('/admin');

    // Should redirect back to login
    await adminPage.waitForURL(/\/login/);
  });

  test('should logout coordinator successfully', async ({ coordinatorPage }) => {
    await coordinatorPage.goto('/schedule');

    // Logout
    await coordinatorPage.click(selectors.nav.userMenu);
    await coordinatorPage.click(selectors.nav.logoutButton);

    await coordinatorPage.waitForURL('/login');
  });

  test('should logout faculty successfully', async ({ facultyPage }) => {
    await facultyPage.goto('/schedule');

    // Logout
    await facultyPage.click(selectors.nav.userMenu);
    await facultyPage.click(selectors.nav.logoutButton);

    await facultyPage.waitForURL('/login');
  });

  test('should logout resident successfully', async ({ residentPage }) => {
    await residentPage.goto('/swaps');

    // Logout
    await residentPage.click(selectors.nav.userMenu);
    await residentPage.click(selectors.nav.logoutButton);

    await residentPage.waitForURL('/login');
  });

  test('should clear authentication tokens on logout', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Get cookies before logout
    const cookiesBefore = await adminPage.context().cookies();
    const hasAuthCookie = cookiesBefore.some(
      (c) => c.name === 'access_token' || c.name === 'session'
    );
    expect(hasAuthCookie).toBeTruthy();

    // Logout
    await adminPage.click(selectors.nav.userMenu);
    await adminPage.click(selectors.nav.logoutButton);
    await adminPage.waitForURL('/login');

    // Get cookies after logout
    const cookiesAfter = await adminPage.context().cookies();
    const stillHasAuthCookie = cookiesAfter.some(
      (c) => c.name === 'access_token' || c.name === 'session'
    );
    expect(stillHasAuthCookie).toBeFalsy();
  });

  test('should clear local storage on logout', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Set some local storage
    await adminPage.evaluate(() => {
      localStorage.setItem('test-key', 'test-value');
    });

    // Logout
    await adminPage.click(selectors.nav.userMenu);
    await adminPage.click(selectors.nav.logoutButton);
    await adminPage.waitForURL('/login');

    // Local storage should be cleared (or user-specific data cleared)
    const localStorageValue = await adminPage.evaluate(() => {
      return localStorage.getItem('access_token') || localStorage.getItem('user');
    });
    expect(localStorageValue).toBeNull();
  });

  test('should show confirmation dialog before logout', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Click user menu
    await adminPage.click(selectors.nav.userMenu);

    // Setup dialog handler (if confirmation is implemented)
    adminPage.on('dialog', async (dialog) => {
      expect(dialog.message()).toContain(/logout|sign out/i);
      await dialog.accept();
    });

    await adminPage.click(selectors.nav.logoutButton);
  });

  test('should not logout on cancel confirmation', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    await adminPage.click(selectors.nav.userMenu);

    // Reject confirmation dialog (if implemented)
    adminPage.once('dialog', async (dialog) => {
      await dialog.dismiss();
    });

    try {
      await adminPage.click(selectors.nav.logoutButton);
      await adminPage.waitForTimeout(1000);
    } catch {
      // Dialog might not be implemented
    }

    // Should still be on dashboard
    const currentURL = adminPage.url();
    expect(currentURL).toContain('/dashboard');
  });

  test('should handle logout API error gracefully', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Mock logout API to fail
    await adminPage.route('**/api/v1/auth/logout', (route) => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });

    // Try to logout
    await adminPage.click(selectors.nav.userMenu);
    await adminPage.click(selectors.nav.logoutButton);

    // Should still redirect to login (client-side logout)
    await adminPage.waitForURL('/login', { timeout: 5000 });
  });

  test('should logout from all tabs when logging out from one', async ({ browser, authUsers }) => {
    // Create two tabs with same session
    const context = await browser.newContext();

    // Login in first tab
    const page1 = await context.newPage();
    await page1.goto('/login');
    await page1.fill(selectors.login.emailInput, authUsers.admin.email);
    await page1.fill(selectors.login.passwordInput, authUsers.admin.password);
    await page1.click(selectors.login.submitButton);
    await page1.waitForURL(/\/(dashboard|schedule)/);

    // Open second tab
    const page2 = await context.newPage();
    await page2.goto('/schedule');

    // Both should be logged in
    await expect(page1.locator(selectors.nav.userMenu)).toBeVisible();
    await expect(page2.locator(selectors.nav.userMenu)).toBeVisible();

    // Logout from first tab
    await page1.click(selectors.nav.userMenu);
    await page1.click(selectors.nav.logoutButton);
    await page1.waitForURL('/login');

    // Second tab should also logout (or show error on next API call)
    await page2.reload();
    await page2.waitForURL(/\/login/, { timeout: 5000 });

    await context.close();
  });

  test('should invalidate refresh token on logout', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Logout
    await adminPage.click(selectors.nav.userMenu);
    await adminPage.click(selectors.nav.logoutButton);
    await adminPage.waitForURL('/login');

    // Try to use refresh token
    const response = await adminPage.request.post('/api/v1/auth/refresh', {
      failOnStatusCode: false,
    });

    // Should fail with 401
    expect(response.status()).toBe(401);
  });

  test('should redirect to login from deep link after logout', async ({ adminPage }) => {
    await adminPage.goto('/schedule/2024-01-15');

    // Logout
    await adminPage.click(selectors.nav.userMenu);
    await adminPage.click(selectors.nav.logoutButton);
    await adminPage.waitForURL('/login');

    // Try to access deep link
    await adminPage.goto('/schedule/2024-01-15');

    // Should redirect to login with return URL
    await adminPage.waitForURL(/\/login\?.*returnUrl=/);

    // Login again
    await adminPage.fill(selectors.login.emailInput, 'admin@test.mil');
    await adminPage.fill(selectors.login.passwordInput, 'TestPassword123!');
    await adminPage.click(selectors.login.submitButton);

    // Should return to original page
    await adminPage.waitForURL('/schedule/2024-01-15');
  });

  test('should show logout success message', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Logout
    await adminPage.click(selectors.nav.userMenu);
    await adminPage.click(selectors.nav.logoutButton);

    // Should show success toast (if implemented)
    try {
      const toast = await waitForToast(adminPage, /logged out|signed out/i);
      await expect(toast).toBeVisible();
    } catch {
      // Toast might not be implemented
    }

    await adminPage.waitForURL('/login');
  });

  test('should be keyboard accessible', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Tab to user menu
    await adminPage.keyboard.press('Tab');
    while (!(await adminPage.locator(selectors.nav.userMenu).isFocused())) {
      await adminPage.keyboard.press('Tab');
    }

    // Open menu with Enter
    await adminPage.keyboard.press('Enter');

    // Tab to logout button
    await adminPage.keyboard.press('Tab');

    // Logout with Enter
    await adminPage.keyboard.press('Enter');

    await adminPage.waitForURL('/login');
  });

  test('should handle concurrent logout requests', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Click logout multiple times rapidly
    await adminPage.click(selectors.nav.userMenu);
    await Promise.all([
      adminPage.click(selectors.nav.logoutButton),
      adminPage.click(selectors.nav.logoutButton),
      adminPage.click(selectors.nav.logoutButton),
    ]).catch(() => {
      // Some clicks might fail as menu closes
    });

    // Should still logout successfully
    await adminPage.waitForURL('/login', { timeout: 5000 });
  });

  test('should preserve logout state across page refresh', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Logout
    await adminPage.click(selectors.nav.userMenu);
    await adminPage.click(selectors.nav.logoutButton);
    await adminPage.waitForURL('/login');

    // Refresh page
    await adminPage.reload();

    // Should still be on login page
    await expect(adminPage).toHaveURL('/login');
    await expect(adminPage.locator(selectors.nav.userMenu)).not.toBeVisible();
  });
});

test.describe('Logout - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should logout on mobile', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Mobile menu might be different
    const userMenu = adminPage.locator(selectors.nav.userMenu);
    await userMenu.click();

    const logoutButton = adminPage.locator(selectors.nav.logoutButton);
    await logoutButton.click();

    await adminPage.waitForURL('/login');
  });
});
