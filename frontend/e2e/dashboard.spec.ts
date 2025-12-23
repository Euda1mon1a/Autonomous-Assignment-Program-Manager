import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and login before each test
<<<<<<< HEAD
    await page.context().clearCookies();
=======
    await page.context().clearPGY2-01ies();
>>>>>>> origin/docs/session-14-summary
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Login with admin credentials
    await page.goto('/login');
    await page.getByLabel('Username').fill('admin');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Wait for dashboard to load
    await page.waitForURL('/', { timeout: 10000 });
  });

  test('should load dashboard with 4 widgets', async ({ page }) => {
    // Verify the dashboard heading is visible
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Verify all 4 dashboard widgets are present
    // 1. Schedule Summary widget
    await expect(page.getByRole('heading', { name: "This Week's Schedule" })).toBeVisible();

    // 2. Compliance Alert widget
    await expect(page.getByText(/Compliance/i)).toBeVisible();

    // 3. Upcoming Absences widget
    await expect(page.getByText(/Upcoming Absences/i)).toBeVisible();

    // 4. Quick Actions widget
    await expect(page.getByRole('heading', { name: 'Quick Actions' })).toBeVisible();
  });

  test('should have Quick Actions buttons that navigate correctly', async ({ page }) => {
    // Test Add Person button navigates to /people
    const addPersonLink = page.getByRole('link', { name: 'Add Person' });
    await expect(addPersonLink).toBeVisible();
    await addPersonLink.click();
    await page.waitForURL('/people', { timeout: 10000 });
    expect(page.url()).toContain('/people');

    // Go back to dashboard
    await page.goto('/');
    await page.waitForURL('/', { timeout: 10000 });

    // Test View Templates button navigates to /templates
    const viewTemplatesLink = page.getByRole('link', { name: 'View Templates' });
    await expect(viewTemplatesLink).toBeVisible();
    await viewTemplatesLink.click();
    await page.waitForURL('/templates', { timeout: 10000 });
    expect(page.url()).toContain('/templates');

    // Go back to dashboard
    await page.goto('/');
    await page.waitForURL('/', { timeout: 10000 });

    // Test Compliance button navigates to /compliance
    const complianceLink = page.getByRole('link', { name: 'Compliance' });
    await expect(complianceLink).toBeVisible();
    await complianceLink.click();
    await page.waitForURL('/compliance', { timeout: 10000 });
    expect(page.url()).toContain('/compliance');
  });

  test('should display Schedule Summary with stats', async ({ page }) => {
    // Wait for the Schedule Summary widget to load
    const scheduleSummary = page.locator('text=This Week\'s Schedule').locator('..');

    // The widget should show either schedule stats or a "no schedule" message
    // Check for either residents scheduled OR no schedule message
    const hasScheduleData = await page.getByText(/residents scheduled/i).isVisible().catch(() => false);
    const hasNoScheduleMessage = await page.getByText(/No schedule generated/i).isVisible().catch(() => false);

    // Either should be true - we have schedule data or a message about no schedule
    expect(hasScheduleData || hasNoScheduleMessage).toBe(true);

    // The "View Full Schedule" link should always be present
    await expect(page.getByRole('link', { name: /View Full Schedule/i })).toBeVisible();
  });

  test('should display Generate Schedule button in Quick Actions', async ({ page }) => {
    // Verify Generate Schedule button is present
    const generateButton = page.getByRole('button', { name: 'Generate Schedule' });
    await expect(generateButton).toBeVisible();

    // Click it to open the dialog
    await generateButton.click();

    // Verify the dialog opens (check for dialog title or content)
    await expect(page.getByText(/Generate Schedule/i).first()).toBeVisible();
  });
});
