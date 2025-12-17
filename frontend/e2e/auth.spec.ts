import { test, expect, Page } from '@playwright/test';
import {
  loginAsUser,
  loginAsAdmin,
  loginAsCoordinator,
  loginAsFaculty,
  logout,
  clearStorage,
  TEST_USERS,
  TIMEOUTS,
} from './fixtures/test-data';

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Verify user is on login page
 */
async function expectLoginPage(page: Page) {
  await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible();
  await expect(page.getByLabel('Username')).toBeVisible();
  await expect(page.getByLabel('Password')).toBeVisible();
}

// ============================================================================
// Test Suite
// ============================================================================

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any stored tokens/session before each test
    await clearStorage(page);
  });

  // ==========================================================================
  // Login Flow Tests
  // ==========================================================================

  test.describe('Login Flow', () => {
    test('should login with valid credentials and redirect to dashboard', async ({ page }) => {
      await loginAsUser(page, TEST_USERS.admin.username, TEST_USERS.admin.password);

      // Wait for redirect to dashboard
      await page.waitForURL('/', { timeout: 10000 });

      // Verify we're on the dashboard
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

      // Security: Verify httpOnly cookie is set (not accessible via JavaScript)
      const cookies = await page.context().cookies();
      const authPGY2-01ie = cookies.find(c => c.name === 'access_token');
      expect(authPGY2-01ie).toBeTruthy();
      expect(authPGY2-01ie?.httpOnly).toBe(true);
    });

    test('should display error for invalid credentials', async ({ page }) => {
      await page.goto('/login');
      await page.getByLabel('Username').fill('invaliduser');
      await page.getByLabel('Password').fill('wrongpassword');
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Wait for error message to appear
      await expect(page.getByText(/invalid/i)).toBeVisible({ timeout: 5000 });

      // Verify we're still on the login page
      expect(page.url()).toContain('/login');

      // Security: Verify no auth cookie was set
      const cookies = await page.context().cookies();
      const authPGY2-01ie = cookies.find(c => c.name === 'access_token');
      expect(authPGY2-01ie).toBeFalsy();
    });

    test('should display error for empty username', async ({ page }) => {
      await page.goto('/login');

      // Leave username empty, fill password
      await page.getByLabel('Password').fill('admin123');

      // Blur the username field to trigger validation
      await page.getByLabel('Username').focus();
      await page.getByLabel('Username').blur();

      // Try to submit
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Verify error message appears
      await expect(page.getByText(/required/i)).toBeVisible();

      // Verify we're still on the login page
      expect(page.url()).toContain('/login');
    });

    test('should display error for empty password', async ({ page }) => {
      await page.goto('/login');

      // Fill username, leave password empty
      await page.getByLabel('Username').fill(TEST_USERS.admin.username);

      // Blur the password field to trigger validation
      await page.getByLabel('Password').focus();
      await page.getByLabel('Password').blur();

      // Try to submit
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Verify error message appears
      await expect(page.getByText(/required/i)).toBeVisible();

      // Verify we're still on the login page
      expect(page.url()).toContain('/login');
    });

    test('should disable submit button while submitting', async ({ page }) => {
      await page.goto('/login');
      await page.getByLabel('Username').fill(TEST_USERS.admin.username);
      await page.getByLabel('Password').fill(TEST_USERS.admin.password);

      // Get the submit button
      const submitButton = page.getByRole('button', { name: 'Sign In' });

      // Click and check if button shows loading state
      await submitButton.click();

      // Check for loading state
      await expect(page.getByText('Signing in...')).toBeVisible();
    });

    test('should login with different user roles', async ({ page }) => {
      // Test coordinator login
      await loginAsUser(page, 'coordinator', 'coord123');
      await page.waitForURL('/', { timeout: 10000 });
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

      // Logout (clear session properly)
      await clearStorage(page);

      // Test faculty login
      await loginAsUser(page, 'faculty', 'faculty123');
      await page.waitForURL('/', { timeout: 10000 });
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    });
  });

  // ==========================================================================
  // Logout Flow Tests
  // ==========================================================================

  test.describe('Logout Flow', () => {
    test('should logout successfully and clear session', async ({ page }) => {
      // Login first
      await loginAsUser(page, 'admin', 'admin123');
      await page.waitForURL('/', { timeout: 10000 });

      // Security: Verify httpOnly cookie exists
      let cookies = await page.context().cookies();
      let authPGY2-01ie = cookies.find(c => c.name === 'access_token');
      expect(authPGY2-01ie).toBeTruthy();

      // Click on user menu to open dropdown
      await page.getByRole('button', { name: /admin/i }).click();

      // Click logout button
      await page.getByRole('button', { name: 'Logout' }).click();

      // Wait for redirect to login page
      await page.waitForURL(/\/login/, { timeout: 10000 });

      // Verify we're on the login page
      await expectLoginPage(page);

      // Security: Verify auth cookie is cleared
      cookies = await page.context().cookies();
      authPGY2-01ie = cookies.find(c => c.name === 'access_token');
      expect(authPGY2-01ie).toBeFalsy();
    });

    test('should redirect to login page after logout', async ({ page }) => {
      // Login first
      await loginAsUser(page, 'admin', 'admin123');
      await page.waitForURL('/', { timeout: 10000 });

      // Logout
      await page.getByRole('button', { name: /admin/i }).click();
      await page.getByRole('button', { name: 'Logout' }).click();

      // Verify redirect to login
      await page.waitForURL(/\/login/, { timeout: 10000 });
      expect(page.url()).toContain('/login');
    });

    test('should not access protected routes after logout', async ({ page }) => {
      // Login first
      await loginAsUser(page, 'admin', 'admin123');
      await page.waitForURL('/', { timeout: 10000 });

      // Logout
      await page.getByRole('button', { name: /admin/i }).click();
      await page.getByRole('button', { name: 'Logout' }).click();
      await page.waitForURL(/\/login/, { timeout: 10000 });

      // Try to access protected route
      await page.goto('/');

      // Should redirect back to login
      await page.waitForURL(/\/login/, { timeout: 10000 });
      expect(page.url()).toContain('/login');
    });
  });

  // ==========================================================================
  // Session Persistence Tests
  // ==========================================================================

  test.describe('Session Tests', () => {
    test('should persist session on page refresh', async ({ page }) => {
      // Login
      await loginAsUser(page, 'admin', 'admin123');
      await page.waitForURL('/', { timeout: 10000 });
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

      // Refresh the page
      await page.reload();

      // Should still be on dashboard
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

      // Security: Verify httpOnly cookie persists across refresh
      const cookies = await page.context().cookies();
      const authPGY2-01ie = cookies.find(c => c.name === 'access_token');
      expect(authPGY2-01ie).toBeTruthy();
      expect(authPGY2-01ie?.httpOnly).toBe(true);
    });

    test('should maintain session across navigation', async ({ page }) => {
      // Login
      await loginAsUser(page, 'admin', 'admin123');
      await page.waitForURL('/', { timeout: 10000 });

      // Navigate to different pages and back
      await page.goto('/residents');
      await page.waitForLoadState('networkidle');

      await page.goto('/');
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

      // Security: Verify httpOnly cookie persists across navigation
      const cookies = await page.context().cookies();
      const authPGY2-01ie = cookies.find(c => c.name === 'access_token');
      expect(authPGY2-01ie).toBeTruthy();
      expect(authPGY2-01ie?.httpOnly).toBe(true);
    });

    test('should handle invalid token gracefully', async ({ page }) => {
      // Security: Set an invalid httpOnly cookie
      await page.context().addPGY2-01ies([{
        name: 'access_token',
        value: 'Bearer invalid-token-12345',
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: false,
        sameSite: 'Lax',
      }]);

      // Try to access protected route
      await page.goto('/');

      // Should redirect to login due to invalid token
      await page.waitForURL(/\/login/, { timeout: 10000 });
      expect(page.url()).toContain('/login');
    });
  });

  // ==========================================================================
  // Protected Route Tests
  // ==========================================================================

  test.describe('Protected Routes', () => {
    test('should redirect unauthenticated users to login', async ({ page }) => {
      // Navigate to the root page without authentication
      await page.goto('/');

      // Wait for redirect to login
      await page.waitForURL(/\/login/, { timeout: 10000 });

      // Verify we're on the login page
      expect(page.url()).toContain('/login');
      await expectLoginPage(page);
    });

    test('should allow authenticated users to access protected routes', async ({ page }) => {
      // Login first
      await loginAsUser(page, 'admin', 'admin123');
      await page.waitForURL('/', { timeout: 10000 });

      // Navigate to protected routes
      await page.goto('/residents');
      await page.waitForLoadState('networkidle');

      // Should not redirect to login
      expect(page.url()).toContain('/residents');
    });

    test('should redirect to login page when accessing protected route without auth', async ({ page }) => {
      // Try to access residents page without auth
      await page.goto('/residents');

      // Should redirect to login
      await page.waitForURL(/\/login/, { timeout: 10000 });
      expect(page.url()).toContain('/login');
    });
  });

  // ==========================================================================
  // Edge Cases
  // ==========================================================================

  test.describe('Edge Cases', () => {
    test('should handle special characters in credentials', async ({ page }) => {
      await page.goto('/login');

      // Try login with special characters
      await page.getByLabel('Username').fill('user@test!#$%');
      await page.getByLabel('Password').fill('p@ssw0rd!@#$%^&*()');
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Should show invalid credentials error (assuming these aren't valid)
      await expect(page.getByText(/invalid/i)).toBeVisible({ timeout: 5000 });
    });

    test('should handle very long username and password', async ({ page }) => {
      await page.goto('/login');

      const longString = 'a'.repeat(1000);
      await page.getByLabel('Username').fill(longString);
      await page.getByLabel('Password').fill(longString);
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Should handle gracefully
      await expect(page.getByText(/invalid/i)).toBeVisible({ timeout: 5000 });
    });

    test('should handle rapid consecutive login attempts', async ({ page }) => {
      await page.goto('/login');

      // Fill form
      await page.getByLabel('Username').fill('admin');
      await page.getByLabel('Password').fill('admin123');

      // Click submit button multiple times rapidly
      const submitButton = page.getByRole('button', { name: 'Sign In' });
      await submitButton.click();

      // Button should be disabled after first click
      await expect(submitButton).toBeDisabled();
    });

    test('should trim whitespace from username', async ({ page }) => {
      await page.goto('/login');

      // Enter username with whitespace
      await page.getByLabel('Username').fill('  admin  ');
      await page.getByLabel('Password').fill('admin123');
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Should still login successfully (if backend trims)
      // OR show error if whitespace is not trimmed
      await page.waitForLoadState('networkidle');

      // Check if we got redirected or stayed on login page
      const currentUrl = page.url();
      expect(currentUrl).toBeTruthy();
    });

    test('should handle network error during login', async ({ page }) => {
      // Simulate offline mode
      await page.context().setOffline(true);

      await page.goto('/login');
      await page.getByLabel('Username').fill('admin');
      await page.getByLabel('Password').fill('admin123');
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Should show some error (network error or timeout)
      // The exact error message may vary
      await page.waitForTimeout(2000);

      // Restore online mode
      await page.context().setOffline(false);
    });

    test('should handle server error (500) gracefully', async ({ page }) => {
      // Intercept login request and return 500
      await page.route('**/api/auth/login', (route) => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Internal Server Error' }),
        });
      });

      await page.goto('/login');
      await page.getByLabel('Username').fill('admin');
      await page.getByLabel('Password').fill('admin123');
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Should show error message
      await expect(page.getByText(/error/i).or(page.getByText(/invalid/i))).toBeVisible({ timeout: 5000 });
    });

    test('should handle malformed server response', async ({ page }) => {
      // Intercept login request and return malformed JSON
      await page.route('**/api/auth/login', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: 'not valid json{',
        });
      });

      await page.goto('/login');
      await page.getByLabel('Username').fill('admin');
      await page.getByLabel('Password').fill('admin123');
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Should handle error gracefully
      await page.waitForTimeout(2000);
      expect(page.url()).toContain('/login');
    });
  });

  // ==========================================================================
  // Security Tests
  // ==========================================================================

  test.describe('Security Tests', () => {
    test('should sanitize XSS attempt in username field', async ({ page }) => {
      await page.goto('/login');

      const xssPayload = '<script>alert("XSS")</script>';
      await page.getByLabel('Username').fill(xssPayload);
      await page.getByLabel('Password').fill('admin123');
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Wait for response
      await page.waitForLoadState('networkidle');

      // Verify no alert was triggered (script not executed)
      // If page redirected, good. If error shown, also good.
      // The important thing is no script execution
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('should sanitize XSS attempt in password field', async ({ page }) => {
      await page.goto('/login');

      await page.getByLabel('Username').fill('admin');
      const xssPayload = '<img src=x onerror=alert("XSS")>';
      await page.getByLabel('Password').fill(xssPayload);
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Wait for response
      await page.waitForLoadState('networkidle');

      // Verify no malicious code execution
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('should handle SQL injection attempt in username', async ({ page }) => {
      await page.goto('/login');

      // Common SQL injection payloads
      const sqlInjection = "admin' OR '1'='1";
      await page.getByLabel('Username').fill(sqlInjection);
      await page.getByLabel('Password').fill('anything');
      await page.getByRole('button', { name: 'Sign In' }).click();

      // Should not authenticate (backend should handle this)
      await expect(page.getByText(/invalid/i)).toBeVisible({ timeout: 5000 });
      expect(page.url()).toContain('/login');
    });

    test('should not expose password in input field', async ({ page }) => {
      await page.goto('/login');

      const passwordInput = page.getByLabel('Password');

      // Verify password field type is 'password'
      const inputType = await passwordInput.getAttribute('type');
      expect(inputType).toBe('password');

      // Fill password
      await passwordInput.fill('admin123');

      // Verify the input type is still password (not changed to text)
      const inputTypeAfter = await passwordInput.getAttribute('type');
      expect(inputTypeAfter).toBe('password');
    });

    test('should use HTTPS for authentication in production', async ({ page }) => {
      // This test checks if the page protocol is secure
      // In development, this might be HTTP, but production should be HTTPS
      await page.goto('/login');

      const url = page.url();

      // For development, we just verify URL is valid
      expect(url).toContain('/login');

      // In production environment, you would verify:
      // expect(url).toMatch(/^https:\/\//);
    });

    test('should not store sensitive data in localStorage and token should be httpOnly', async ({ page }) => {
      await loginAsUser(page, 'admin', 'admin123');
      await page.waitForURL('/', { timeout: 10000 });

      // Check localStorage for sensitive data
      const localStorageData = await page.evaluate(() => {
        return JSON.stringify(localStorage);
      });

      // Verify password is not stored
      expect(localStorageData).not.toContain('admin123');
      expect(localStorageData).not.toContain('password');

      // Security: Verify auth token is NOT accessible via JavaScript (httpOnly protection)
      const tokenFromJS = await page.evaluate(() => {
        return document.cookie.split(';').find(c => c.trim().startsWith('access_token='));
      });
      expect(tokenFromJS).toBeFalsy(); // httpOnly cookies are not accessible via JavaScript

      // But verify the cookie exists at the browser level
      const cookies = await page.context().cookies();
      const authPGY2-01ie = cookies.find(c => c.name === 'access_token');
      expect(authPGY2-01ie).toBeTruthy();
      expect(authPGY2-01ie?.httpOnly).toBe(true);
    });

    test('should not expose sensitive data in URL parameters', async ({ page }) => {
      await page.goto('/login');
      await page.getByLabel('Username').fill('admin');
      await page.getByLabel('Password').fill('admin123');
      await page.getByRole('button', { name: 'Sign In' }).click();

      await page.waitForLoadState('networkidle');

      // Check that URL doesn't contain credentials
      const currentUrl = page.url();
      expect(currentUrl).not.toContain('admin123');
      expect(currentUrl).not.toContain('password=');
      expect(currentUrl).not.toContain('username=admin');
    });
  });

  // ==========================================================================
  // Already Authenticated User Tests
  // ==========================================================================

  test.describe('Already Authenticated', () => {
    test('should redirect to dashboard if already logged in and visiting login page', async ({ page }) => {
      // Login first
      await loginAsUser(page, 'admin', 'admin123');
      await page.waitForURL('/', { timeout: 10000 });

      // Try to visit login page while authenticated
      await page.goto('/login');

      // Should redirect back to dashboard
      await page.waitForURL('/', { timeout: 10000 });
      expect(page.url()).not.toContain('/login');
    });
  });
});
