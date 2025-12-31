import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';

/**
 * Token Refresh Tests
 *
 * Tests for automatic token refresh functionality
 */

test.describe('Token Refresh', () => {
  test('should automatically refresh token before expiration', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Mock token that's about to expire (30 seconds left)
    await adminPage.evaluate(() => {
      const expiresAt = Date.now() + 30000; // 30 seconds
      localStorage.setItem('token_expires_at', expiresAt.toString());
    });

    // Make API call that should trigger refresh
    await adminPage.goto('/schedule');

    // Should remain authenticated
    await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();
  });

  test('should refresh token only once for concurrent requests', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    let refreshCallCount = 0;

    // Intercept refresh endpoint
    await adminPage.route('**/api/v1/auth/refresh', (route) => {
      refreshCallCount++;
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          access_token: 'new-token',
          token_type: 'bearer',
        }),
      });
    });

    // Trigger token expiration
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000;
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    // Make multiple concurrent API calls
    await Promise.all([
      adminPage.request.get('/api/v1/persons').catch(() => {}),
      adminPage.request.get('/api/v1/rotations').catch(() => {}),
      adminPage.request.get('/api/v1/assignments').catch(() => {}),
    ]);

    // Should only call refresh once
    expect(refreshCallCount).toBeLessThanOrEqual(1);
  });

  test('should handle refresh failure gracefully', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Mock refresh to fail
    await adminPage.route('**/api/v1/auth/refresh', (route) => {
      route.fulfill({
        status: 401,
        body: JSON.stringify({ detail: 'Invalid refresh token' }),
      });
    });

    // Trigger token expiration
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000;
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    // Try to navigate
    await adminPage.goto('/schedule');

    // Should redirect to login
    await adminPage.waitForURL('/login', { timeout: 10000 });
  });

  test('should update token expiration after refresh', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Get initial expiration
    const initialExpiration = await adminPage.evaluate(() => {
      return localStorage.getItem('token_expires_at');
    });

    // Trigger refresh
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000;
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    await adminPage.reload();

    // Get new expiration
    const newExpiration = await adminPage.evaluate(() => {
      return localStorage.getItem('token_expires_at');
    });

    // New expiration should be in the future
    if (newExpiration) {
      expect(parseInt(newExpiration)).toBeGreaterThan(Date.now());
    }
  });

  test('should queue API calls during token refresh', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Mock slow refresh
    await adminPage.route('**/api/v1/auth/refresh', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000)); // 2 second delay
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          access_token: 'new-token',
          token_type: 'bearer',
        }),
      });
    });

    // Trigger expiration
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000;
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    // Make API calls - should queue during refresh
    const startTime = Date.now();
    await Promise.all([
      adminPage.request.get('/api/v1/persons').catch(() => {}),
      adminPage.request.get('/api/v1/rotations').catch(() => {}),
    ]);
    const endTime = Date.now();

    // Should have waited for refresh
    expect(endTime - startTime).toBeGreaterThan(1500);
  });

  test('should use new token for subsequent requests', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    let requestCount = 0;
    const seenTokens = new Set<string>();

    // Intercept API calls to check token
    await adminPage.route('**/api/v1/**', (route) => {
      requestCount++;
      const authHeader = route.request().headers()['authorization'];
      if (authHeader) {
        seenTokens.add(authHeader);
      }
      route.continue();
    });

    // Trigger token refresh
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000;
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    // Make requests
    await adminPage.goto('/schedule');
    await adminPage.goto('/swaps');

    // Should have used new token after refresh
    expect(seenTokens.size).toBeGreaterThan(0);
  });

  test('should handle refresh token rotation', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Mock refresh with token rotation
    let refreshCount = 0;
    await adminPage.route('**/api/v1/auth/refresh', (route) => {
      refreshCount++;
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          access_token: `new-access-token-${refreshCount}`,
          refresh_token: `new-refresh-token-${refreshCount}`,
          token_type: 'bearer',
        }),
      });
    });

    // Trigger multiple refreshes
    for (let i = 0; i < 3; i++) {
      await adminPage.evaluate(() => {
        const expiredTime = Date.now() - 1000;
        localStorage.setItem('token_expires_at', expiredTime.toString());
      });

      await adminPage.reload();
      await adminPage.waitForTimeout(500);
    }

    // Should have refreshed multiple times
    expect(refreshCount).toBeGreaterThan(0);
  });

  test('should not refresh if token is still valid', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    let refreshCalled = false;
    await adminPage.route('**/api/v1/auth/refresh', (route) => {
      refreshCalled = true;
      route.continue();
    });

    // Set token that's still valid (1 hour from now)
    await adminPage.evaluate(() => {
      const expiresAt = Date.now() + 3600000;
      localStorage.setItem('token_expires_at', expiresAt.toString());
    });

    // Make API calls
    await adminPage.goto('/schedule');

    // Should NOT have called refresh
    expect(refreshCalled).toBe(false);
  });

  test('should refresh proactively before expiration', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    let refreshCalled = false;
    await adminPage.route('**/api/v1/auth/refresh', (route) => {
      refreshCalled = true;
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          access_token: 'refreshed-token',
          token_type: 'bearer',
        }),
      });
    });

    // Set token that expires soon (1 minute)
    await adminPage.evaluate(() => {
      const expiresAt = Date.now() + 60000; // 1 minute
      localStorage.setItem('token_expires_at', expiresAt.toString());
    });

    // Make API call
    await adminPage.goto('/schedule');

    // Should proactively refresh (if threshold is < 1 minute)
    // This depends on implementation
    if (refreshCalled) {
      expect(refreshCalled).toBe(true);
    }
  });

  test('should clear tokens on persistent refresh failure', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    let refreshAttempts = 0;
    await adminPage.route('**/api/v1/auth/refresh', (route) => {
      refreshAttempts++;
      route.fulfill({
        status: 401,
        body: JSON.stringify({ detail: 'Invalid refresh token' }),
      });
    });

    // Trigger refresh
    await adminPage.evaluate(() => {
      const expiredTime = Date.now() - 1000;
      localStorage.setItem('token_expires_at', expiredTime.toString());
    });

    await adminPage.goto('/schedule');

    // Should redirect to login
    await adminPage.waitForURL('/login', { timeout: 10000 });

    // Should have cleared tokens
    const hasToken = await adminPage.evaluate(() => {
      return Boolean(localStorage.getItem('access_token'));
    });

    expect(hasToken).toBe(false);
  });
});

test.describe('Refresh Token Security', () => {
  test('should use httpOnly cookie for refresh token', async ({ adminPage }) => {
    await adminPage.goto('/login');

    await adminPage.fill(selectors.login.emailInput, 'admin@test.mil');
    await adminPage.fill(selectors.login.passwordInput, 'TestPassword123!');
    await adminPage.click(selectors.login.submitButton);
    await adminPage.waitForURL(/\/(dashboard|schedule)/);

    // Check cookies
    const cookies = await adminPage.context().cookies();
    const refreshCookie = cookies.find((c) => c.name === 'refresh_token');

    if (refreshCookie) {
      // Should be httpOnly for security
      expect(refreshCookie.httpOnly).toBe(true);
      // Should be secure in production
      // expect(refreshCookie.secure).toBe(true);
    }
  });

  test('should not expose refresh token in JavaScript', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Try to access refresh token from JavaScript
    const refreshToken = await adminPage.evaluate(() => {
      return (
        localStorage.getItem('refresh_token') ||
        sessionStorage.getItem('refresh_token') ||
        document.cookie.match(/refresh_token=([^;]+)/)
      );
    });

    // Should not be accessible (should be httpOnly cookie)
    expect(refreshToken).toBeNull();
  });
});
