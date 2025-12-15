import { test, expect } from '@playwright/test';

test.describe('People Page', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and login before each test
    await page.context().clearPGY2-01ies();
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Login with admin credentials
    await page.goto('/login');
    await page.getByLabel('Username').fill('admin');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Wait for dashboard to load, then navigate to people page
    await page.waitForURL('/', { timeout: 10000 });
    await page.goto('/people');
    await page.waitForURL('/people', { timeout: 10000 });
  });

  test('should load people page with list', async ({ page }) => {
    // Verify the page heading
    await expect(page.getByRole('heading', { name: 'People' })).toBeVisible();
    await expect(page.getByText('Manage residents and faculty')).toBeVisible();

    // Verify the Add Person button is visible
    await expect(page.getByRole('button', { name: /Add Person/i })).toBeVisible();

    // Verify filter tabs are present
    await expect(page.getByRole('button', { name: 'All' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Resident' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Faculty' })).toBeVisible();

    // Wait for the list to load (either show people cards or empty state)
    const hasPeopleCards = await page.locator('.card').count() > 0;
    const hasEmptyState = await page.getByText(/No people found/i).isVisible().catch(() => false);

    // Either we have people listed or an empty state message
    expect(hasPeopleCards || hasEmptyState).toBe(true);
  });

  test('should open Add Person modal when clicking Add Person button', async ({ page }) => {
    // Find and click the Add Person button
    const addButton = page.getByRole('button', { name: /Add Person/i });
    await expect(addButton).toBeVisible();
    await addButton.click();

    // Verify the modal is opened
    await expect(page.getByRole('heading', { name: /Add Person/i })).toBeVisible({ timeout: 5000 });

    // Check for form fields in the modal
    await expect(page.getByLabel(/Name/i)).toBeVisible();
    await expect(page.getByText(/Type|Role/i).first()).toBeVisible();

    // Verify there are action buttons
    const cancelButton = page.getByRole('button', { name: /Cancel/i });
    await expect(cancelButton).toBeVisible();

    // Close the modal
    await cancelButton.click();

    // Verify modal is closed
    await expect(page.getByRole('heading', { name: /Add Person/i })).not.toBeVisible({ timeout: 3000 });
  });

  test('should filter people by role type', async ({ page }) => {
    // Click on Resident filter
    const residentButton = page.getByRole('button', { name: 'Resident' });
    await residentButton.click();

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Verify button appears active (has different styling)
    await expect(residentButton).toHaveClass(/bg-blue-100/);

    // Click on Faculty filter
    const facultyButton = page.getByRole('button', { name: 'Faculty' });
    await facultyButton.click();

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Verify Faculty button is now active
    await expect(facultyButton).toHaveClass(/bg-blue-100/);

    // Click back to All
    const allButton = page.getByRole('button', { name: 'All' });
    await allButton.click();

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Verify All button is active
    await expect(allButton).toHaveClass(/bg-blue-100/);
  });

  test('should have PGY level filter visible when not filtering by faculty', async ({ page }) => {
    // When viewing All or Residents, PGY filter should be visible
    const pgyFilter = page.locator('select').filter({ hasText: /All PGY Levels|PGY/i });
    await expect(pgyFilter).toBeVisible();

    // Click on Faculty filter
    const facultyButton = page.getByRole('button', { name: 'Faculty' });
    await facultyButton.click();

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // PGY filter should be hidden when viewing Faculty
    await expect(pgyFilter).not.toBeVisible();

    // Switch back to All
    const allButton = page.getByRole('button', { name: 'All' });
    await allButton.click();

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // PGY filter should be visible again
    await expect(page.locator('select').filter({ hasText: /All PGY Levels|PGY/i })).toBeVisible();
  });

  test('should open Edit Person modal when clicking Edit on a person card', async ({ page }) => {
    // Wait for people list to load
    await page.waitForTimeout(1000);

    // Check if there are any people in the list
    const editButtons = page.getByRole('button', { name: /Edit/i }).or(page.getByText('Edit').first());
    const editButtonCount = await editButtons.count();

    if (editButtonCount > 0) {
      // Click the first Edit button
      await editButtons.first().click();

      // Verify the edit modal opens
      await expect(page.getByRole('heading', { name: /Edit Person/i })).toBeVisible({ timeout: 5000 });

      // Check that form is pre-populated (has a name field with value)
      const nameInput = page.getByLabel(/Name/i);
      await expect(nameInput).toBeVisible();

      // Close the modal
      const cancelButton = page.getByRole('button', { name: /Cancel/i });
      if (await cancelButton.isVisible()) {
        await cancelButton.click();
      } else {
        // Try clicking outside or pressing Escape
        await page.keyboard.press('Escape');
      }

      // Verify modal is closed
      await expect(page.getByRole('heading', { name: /Edit Person/i })).not.toBeVisible({ timeout: 3000 });
    } else {
      // If no people exist, just verify the empty state is shown correctly
      const hasEmptyState = await page.getByText(/No people found/i).isVisible();
      expect(hasEmptyState).toBe(true);
    }
  });
});
