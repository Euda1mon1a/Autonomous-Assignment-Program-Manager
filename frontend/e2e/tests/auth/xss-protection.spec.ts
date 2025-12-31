import { test, expect } from '../../fixtures/auth.fixture';

/**
 * XSS Protection Tests
 *
 * Tests for Cross-Site Scripting protection
 */

test.describe('XSS Protection', () => {
  test('should escape HTML in user input', async ({ adminPage }) => {
    await adminPage.goto('/schedule/new');

    const xssPayload = '<script>alert("XSS")</script>';

    // Try to inject XSS in form field
    await adminPage.fill('textarea[name="notes"]', xssPayload);
    await adminPage.click('button[type="submit"]');

    // Check if script was escaped
    await adminPage.waitForTimeout(1000);

    const scriptTags = await adminPage.locator('script:has-text("alert")').count();
    expect(scriptTags).toBe(0);
  });

  test('should sanitize HTML in rendered content', async ({ adminPage }) => {
    await adminPage.goto('/schedule');

    // Check if any user-generated content is properly sanitized
    const content = await adminPage.content();

    // Should not contain unescaped script tags
    expect(content).not.toContain('<script>alert');
    expect(content).not.toContain('onerror=');
    expect(content).not.toContain('onclick=alert');
  });

  test('should encode URLs to prevent javascript: URLs', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Check all links
    const links = await adminPage.locator('a').all();

    for (const link of links) {
      const href = await link.getAttribute('href');
      if (href) {
        expect(href).not.toMatch(/^javascript:/i);
        expect(href).not.toMatch(/^data:/i);
      }
    }
  });

  test('should use Content Security Policy', async ({ adminPage }) => {
    const response = await adminPage.goto('/dashboard');

    const csp = response?.headers()['content-security-policy'];
    expect(csp).toBeTruthy();

    // Should not allow inline scripts
    if (csp) {
      expect(csp).not.toContain("'unsafe-inline'");
      expect(csp).not.toContain("'unsafe-eval'");
    }
  });

  test('should sanitize SVG content', async ({ adminPage }) => {
    await adminPage.goto('/schedule');

    // If SVG icons are used, check they don't contain scripts
    const svgs = await adminPage.locator('svg').all();

    for (const svg of svgs) {
      const content = await svg.innerHTML();
      expect(content).not.toContain('<script');
      expect(content).not.toContain('onerror');
    }
  });

  test('should prevent DOM-based XSS', async ({ adminPage }) => {
    // Try to inject XSS via URL parameter
    await adminPage.goto('/search?q=<script>alert("XSS")</script>');

    await adminPage.waitForTimeout(500);

    // Check if script was executed
    const scriptTags = await adminPage.locator('script:has-text("alert")').count();
    expect(scriptTags).toBe(0);

    // Check if it was properly escaped in DOM
    const bodyHTML = await adminPage.locator('body').innerHTML();
    expect(bodyHTML).not.toContain('<script>alert("XSS")</script>');
  });

  test('should escape JSON data in inline scripts', async ({ adminPage }) => {
    const response = await adminPage.goto('/dashboard');

    const content = await response?.text();

    if (content) {
      // Check for proper escaping in inline JSON
      const inlineScripts = content.match(/<script[^>]*>([\s\S]*?)<\/script>/gi);

      if (inlineScripts) {
        for (const script of inlineScripts) {
          // Should not contain unescaped user data
          expect(script).not.toContain('</script><script>');
        }
      }
    }
  });

  test('should validate and sanitize file uploads', async ({ adminPage }) => {
    await adminPage.goto('/import');

    const fileInput = adminPage.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      // Should have file type restrictions
      const accept = await fileInput.getAttribute('accept');
      expect(accept).toBeTruthy();

      // Should not allow .html, .js files
      if (accept) {
        expect(accept).not.toContain('.html');
        expect(accept).not.toContain('.js');
      }
    }
  });
});
