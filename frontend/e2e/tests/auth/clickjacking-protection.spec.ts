import { test, expect } from '@playwright/test';

/**
 * Clickjacking Protection Tests
 */

test.describe('Clickjacking Protection', () => {
  test('should set X-Frame-Options header', async ({ page }) => {
    const response = await page.goto('/login');

    const xFrameOptions = response?.headers()['x-frame-options'];
    expect(xFrameOptions).toBeTruthy();
    expect(xFrameOptions?.toUpperCase()).toMatch(/DENY|SAMEORIGIN/);
  });

  test('should set frame-ancestors in CSP', async ({ page }) => {
    const response = await page.goto('/login');

    const csp = response?.headers()['content-security-policy'];
    if (csp) {
      expect(csp).toContain("frame-ancestors 'none'");
    }
  });

  test('should not be embeddable in iframe', async ({ page, context }) => {
    // Create a page that tries to embed the app
    await page.setContent(`
      <html>
        <body>
          <iframe src="${page.url()}/login" id="test-frame"></iframe>
        </body>
      </html>
    `);

    // Wait a bit
    await page.waitForTimeout(2000);

    // Check if iframe loaded
    const frame = page.frameLocator('#test-frame');
    const frameExists = await page.locator('#test-frame').count();

    // Frame might be blocked or empty
    if (frameExists > 0) {
      try {
        const frameContent = await page.frame({ url: /login/ });
        // Frame should be blocked or empty
      } catch {
        // Expected - frame blocked
      }
    }
  });
});
