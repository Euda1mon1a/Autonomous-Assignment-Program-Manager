import { test, expect } from '@playwright/test';

/**
 * Security Headers Tests
 *
 * Tests for security-related HTTP headers
 */

test.describe('Security Headers', () => {
  test('should include Content-Security-Policy header', async ({ page }) => {
    const response = await page.goto('/');

    const csp = response?.headers()['content-security-policy'];
    expect(csp).toBeTruthy();
    expect(csp).toContain("default-src 'self'");
  });

  test('should include X-Frame-Options header', async ({ page }) => {
    const response = await page.goto('/');

    const xFrame = response?.headers()['x-frame-options'];
    expect(xFrame).toBeTruthy();
    expect(xFrame?.toLowerCase()).toMatch(/deny|sameorigin/);
  });

  test('should include X-Content-Type-Options header', async ({ page }) => {
    const response = await page.goto('/');

    const xContentType = response?.headers()['x-content-type-options'];
    expect(xContentType).toBe('nosniff');
  });

  test('should include Strict-Transport-Security header', async ({ page }) => {
    const response = await page.goto('/');

    const hsts = response?.headers()['strict-transport-security'];
    if (process.env.NODE_ENV === 'production') {
      expect(hsts).toBeTruthy();
      expect(hsts).toContain('max-age');
    }
  });

  test('should include X-XSS-Protection header', async ({ page }) => {
    const response = await page.goto('/');

    const xss = response?.headers()['x-xss-protection'];
    expect(xss).toBeTruthy();
  });

  test('should include Referrer-Policy header', async ({ page }) => {
    const response = await page.goto('/');

    const referrer = response?.headers()['referrer-policy'];
    expect(referrer).toBeTruthy();
  });

  test('should not expose server information', async ({ page }) => {
    const response = await page.goto('/');

    const server = response?.headers()['server'];
    const xPoweredBy = response?.headers()['x-powered-by'];

    // Should not reveal server details
    if (server) {
      expect(server.toLowerCase()).not.toContain('apache/');
      expect(server.toLowerCase()).not.toContain('nginx/');
    }
    expect(xPoweredBy).toBeFalsy();
  });

  test('should include Permissions-Policy header', async ({ page }) => {
    const response = await page.goto('/');

    const permissionsPolicy = response?.headers()['permissions-policy'];
    if (permissionsPolicy) {
      expect(permissionsPolicy).toBeTruthy();
    }
  });
});
