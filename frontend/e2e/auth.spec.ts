import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any stored tokens/session before each test
    await page.context().clearCookies();
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('should redirect to /login when navigating to / without authentication', async ({ page }) => {
    // Navigate to the root page
    await page.goto('/');

    // Wait for potential redirect
    await page.waitForURL(/\/login/, { timeout: 10000 });

    // Verify we're on the login page
    expect(page.url()).toContain('/login');

    // Verify login page elements are visible
    await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible();
    await expect(page.getByLabel('Username')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
  });

  test('should login with valid credentials and redirect to dashboard', async ({ page }) => {
    // Go to login page
    await page.goto('/login');

    // Fill in the login form with demo admin credentials
    await page.getByLabel('Username').fill('admin');
    await page.getByLabel('Password').fill('admin123');

    // Click the sign in button
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Wait for redirect to dashboard
    await page.waitForURL('/', { timeout: 10000 });

    // Verify we're on the dashboard
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should show error message with invalid credentials', async ({ page }) => {
    // Go to login page
    await page.goto('/login');

    // Fill in the login form with invalid credentials
    await page.getByLabel('Username').fill('invaliduser');
    await page.getByLabel('Password').fill('wrongpassword');

    // Click the sign in button
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Wait for error message to appear
    await expect(page.getByText(/invalid/i)).toBeVisible({ timeout: 5000 });

    // Verify we're still on the login page
    expect(page.url()).toContain('/login');
  });

  test('should logout and redirect to login page', async ({ page }) => {
    // First, login with valid credentials
    await page.goto('/login');
    await page.getByLabel('Username').fill('admin');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Wait for redirect to dashboard
    await page.waitForURL('/', { timeout: 10000 });

    // Verify we're logged in by checking for dashboard
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Click on user menu to open dropdown
    await page.getByRole('button', { name: /admin/i }).click();

    // Click logout button
    await page.getByRole('button', { name: 'Logout' }).click();

    // Wait for redirect to login page
    await page.waitForURL(/\/login/, { timeout: 10000 });

    // Verify we're on the login page
    expect(page.url()).toContain('/login');
    await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible();

    // Verify that going to dashboard redirects back to login (session cleared)
    await page.goto('/');
    await page.waitForURL(/\/login/, { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });
});
