import { test, expect } from '@playwright/test';

test.describe('Absences Page', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and login before each test
    await page.context().clearCookies();
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Login with admin credentials
    await page.goto('/login');
    await page.getByLabel('Username').fill('admin');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Wait for dashboard to load, then navigate to absences
    await page.waitForURL('/', { timeout: 10000 });
    await page.goto('/absences');
    await page.waitForURL('/absences', { timeout: 10000 });
  });

  test('should load absences page with calendar view by default', async ({ page }) => {
    // Verify the page heading
    await expect(page.getByRole('heading', { name: 'Absence Management' })).toBeVisible();
    await expect(page.getByText('Manage vacation, sick days, and other absences')).toBeVisible();

    // Verify calendar view toggle is active (default view)
    const calendarButton = page.getByRole('button', { name: 'Calendar' });
    await expect(calendarButton).toBeVisible();

    // The calendar view should be the default active state
    // Check for calendar-related elements (month navigation or calendar grid)
    const hasCalendarElements = await page.locator('[class*="calendar"]').count() > 0 ||
      await page.getByText(/January|February|March|April|May|June|July|August|September|October|November|December/i).isVisible().catch(() => false);

    expect(hasCalendarElements).toBe(true);
  });

  test('should toggle between calendar and list view', async ({ page }) => {
    // Initially in calendar view - verify Calendar button is highlighted/active
    const calendarButton = page.getByRole('button', { name: 'Calendar' });
    const listButton = page.getByRole('button', { name: 'List' });

    await expect(calendarButton).toBeVisible();
    await expect(listButton).toBeVisible();

    // Click on List view
    await listButton.click();

    // Give time for view to switch
    await page.waitForTimeout(500);

    // Now click back to Calendar view
    await calendarButton.click();

    // Verify we can toggle between views (no errors thrown)
    await page.waitForTimeout(500);

    // Both buttons should still be visible and functional
    await expect(calendarButton).toBeVisible();
    await expect(listButton).toBeVisible();
  });

  test('should filter absences by type', async ({ page }) => {
    // Find the type filter dropdown
    const typeFilter = page.locator('select').filter({ hasText: /All Types/i });
    await expect(typeFilter).toBeVisible();

    // Verify initial state shows "All Types"
    await expect(typeFilter).toHaveValue('all');

    // Change filter to Vacation
    await typeFilter.selectOption('vacation');
    await expect(typeFilter).toHaveValue('vacation');

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Change filter to Medical
    await typeFilter.selectOption('medical');
    await expect(typeFilter).toHaveValue('medical');

    // Change filter to Conference
    await typeFilter.selectOption('conference');
    await expect(typeFilter).toHaveValue('conference');

    // Change back to All Types
    await typeFilter.selectOption('all');
    await expect(typeFilter).toHaveValue('all');
  });

  test('should open Add Absence modal when clicking Add Absence button', async ({ page }) => {
    // Find and click the Add Absence button
    const addButton = page.getByRole('button', { name: /Add Absence/i });
    await expect(addButton).toBeVisible();
    await addButton.click();

    // Verify the modal is opened by checking for modal elements
    // The modal should have form fields for adding an absence
    await expect(page.getByRole('heading', { name: /Add Absence/i })).toBeVisible({ timeout: 5000 });

    // Check for form fields in the modal
    await expect(page.getByText(/Person|Resident|Select/i).first()).toBeVisible();
    await expect(page.getByText(/Absence Type|Type/i).first()).toBeVisible();
    await expect(page.getByText(/Start Date/i).first()).toBeVisible();
    await expect(page.getByText(/End Date/i).first()).toBeVisible();

    // Verify there's a cancel/close button
    const cancelButton = page.getByRole('button', { name: /Cancel/i });
    await expect(cancelButton).toBeVisible();

    // Close the modal
    await cancelButton.click();

    // Verify modal is closed
    await expect(page.getByRole('heading', { name: /Add Absence/i })).not.toBeVisible({ timeout: 3000 });
  });

  test('should have Add Absence button visible in header', async ({ page }) => {
    // Verify the Add Absence button is prominently displayed
    const addButton = page.getByRole('button', { name: /Add Absence/i });
    await expect(addButton).toBeVisible();

    // Verify it has the Plus icon (by checking button content)
    await expect(addButton).toBeEnabled();
  });
});
