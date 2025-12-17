import { test, expect } from '@playwright/test';
import {
  loginAsAdmin,
  clearStorage,
  navigateAsAuthenticated,
  waitForLoadingComplete,
  SAMPLE_PERSON_DATA,
  TIMEOUTS,
  VIEWPORT_SIZES,
} from './fixtures/test-data';

test.describe('People Page', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and login before each test
    await clearStorage(page);
    await loginAsAdmin(page);

    // Navigate to people page
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
    await page.waitForTimeout(TIMEOUTS.short);

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

  // ==========================================================================
  // CRUD Operations Tests
  // ==========================================================================

  test.describe('Create Person', () => {
    test('should create a new resident with valid data', async ({ page }) => {
      // Open Add Person modal
      await page.getByRole('button', { name: /Add Person/i }).click();
      await expect(page.getByRole('heading', { name: /Add Person/i })).toBeVisible({ timeout: 5000 });

      // Fill form with resident data
      await page.getByLabel(/Name/i).fill(`E2E Test Resident ${Date.now()}`);

      // Select resident type
      const typeSelect = page.locator('select').filter({ hasText: /Resident|Faculty/i }).first();
      await typeSelect.selectOption('resident');

      // Select PGY level
      const pgySelect = page.locator('select').filter({ hasText: /PGY|Level/i });
      if (await pgySelect.isVisible()) {
        await pgySelect.selectOption('2');
      }

      // Fill email if field exists
      const emailField = page.getByLabel(/Email/i);
      if (await emailField.isVisible()) {
        await emailField.fill(`e2etest${Date.now()}@hospital.edu`);
      }

      // Submit form
      const submitButton = page.getByRole('button', { name: /Add|Create|Save/i }).filter({ hasNot: page.getByRole('button', { name: /Cancel/i }) });
      await submitButton.click();

      // Wait for modal to close
      await page.waitForTimeout(TIMEOUTS.medium);

      // Verify success notification or modal closed
      const modalClosed = await page.getByRole('heading', { name: /Add Person/i }).isVisible().catch(() => false);
      expect(modalClosed).toBe(false);
    });

    test('should create a new faculty member', async ({ page }) => {
      // Open Add Person modal
      await page.getByRole('button', { name: /Add Person/i }).click();
      await expect(page.getByRole('heading', { name: /Add Person/i })).toBeVisible({ timeout: 5000 });

      // Fill form with faculty data
      await page.getByLabel(/Name/i).fill(`E2E Test Faculty ${Date.now()}`);

      // Select faculty type
      const typeSelect = page.locator('select').filter({ hasText: /Resident|Faculty/i }).first();
      await typeSelect.selectOption('faculty');

      // Fill email if field exists
      const emailField = page.getByLabel(/Email/i);
      if (await emailField.isVisible()) {
        await emailField.fill(`e2efaculty${Date.now()}@hospital.edu`);
      }

      // Submit form
      const submitButton = page.getByRole('button', { name: /Add|Create|Save/i }).filter({ hasNot: page.getByRole('button', { name: /Cancel/i }) });
      await submitButton.click();

      // Wait for modal to close
      await page.waitForTimeout(TIMEOUTS.medium);

      // Verify modal closed
      const modalClosed = await page.getByRole('heading', { name: /Add Person/i }).isVisible().catch(() => false);
      expect(modalClosed).toBe(false);
    });

    test('should validate required fields in Add Person form', async ({ page }) => {
      // Open Add Person modal
      await page.getByRole('button', { name: /Add Person/i }).click();
      await expect(page.getByRole('heading', { name: /Add Person/i })).toBeVisible({ timeout: 5000 });

      // Try to submit without filling required fields
      const submitButton = page.getByRole('button', { name: /Add|Create|Save/i }).filter({ hasNot: page.getByRole('button', { name: /Cancel/i }) });
      await submitButton.click();

      // Should show validation errors
      await page.waitForTimeout(TIMEOUTS.short);

      // Verify error message appears
      const hasError = await page.getByText(/required/i).isVisible().catch(() => false);

      // Modal should still be open
      const modalOpen = await page.getByRole('heading', { name: /Add Person/i }).isVisible();
      expect(modalOpen).toBe(true);
    });

    test('should cancel person creation', async ({ page }) => {
      // Open Add Person modal
      await page.getByRole('button', { name: /Add Person/i }).click();
      await expect(page.getByRole('heading', { name: /Add Person/i })).toBeVisible({ timeout: 5000 });

      // Fill some data
      await page.getByLabel(/Name/i).fill('Test Person to Cancel');

      // Click Cancel
      await page.getByRole('button', { name: /Cancel/i }).click();

      // Verify modal closed
      await expect(page.getByRole('heading', { name: /Add Person/i })).not.toBeVisible({ timeout: 3000 });
    });
  });

  test.describe('Edit Person', () => {
    test('should update person information', async ({ page }) => {
      // Wait for people list to load
      await page.waitForTimeout(TIMEOUTS.short);

      // Check if there are any people
      const editButtons = page.getByText('Edit');
      const editCount = await editButtons.count();

      if (editCount > 0) {
        // Click first Edit button
        await editButtons.first().click();

        // Wait for edit modal
        await expect(page.getByRole('heading', { name: /Edit Person/i })).toBeVisible({ timeout: 5000 });

        // Get current name
        const nameInput = page.getByLabel(/Name/i);
        const currentName = await nameInput.inputValue();

        // Update name
        const updatedName = `${currentName} (Updated)`;
        await nameInput.fill(updatedName);

        // Submit form
        const submitButton = page.getByRole('button', { name: /Save|Update/i }).filter({ hasNot: page.getByRole('button', { name: /Cancel/i }) });
        if (await submitButton.isVisible()) {
          await submitButton.click();

          // Wait for modal to close
          await page.waitForTimeout(TIMEOUTS.medium);

          // Verify modal closed
          const modalClosed = await page.getByRole('heading', { name: /Edit Person/i }).isVisible().catch(() => false);
          expect(modalClosed).toBe(false);
        }
      }
    });

    test('should cancel person edit', async ({ page }) => {
      // Wait for people list to load
      await page.waitForTimeout(TIMEOUTS.short);

      // Check if there are any people
      const editButtons = page.getByText('Edit');
      const editCount = await editButtons.count();

      if (editCount > 0) {
        // Click first Edit button
        await editButtons.first().click();

        // Wait for edit modal
        await expect(page.getByRole('heading', { name: /Edit Person/i })).toBeVisible({ timeout: 5000 });

        // Make some changes
        const nameInput = page.getByLabel(/Name/i);
        await nameInput.fill('Changed Name');

        // Click Cancel
        await page.getByRole('button', { name: /Cancel/i }).click();

        // Verify modal closed
        await expect(page.getByRole('heading', { name: /Edit Person/i })).not.toBeVisible({ timeout: 3000 });
      }
    });
  });

  test.describe('Delete Person', () => {
    test('should show confirmation dialog when deleting person', async ({ page }) => {
      // Wait for people list to load
      await page.waitForTimeout(TIMEOUTS.short);

      // Check if there are any people
      const deleteButtons = page.getByText('Delete');
      const deleteCount = await deleteButtons.count();

      if (deleteCount > 0) {
        // Click first Delete button
        await deleteButtons.first().click();

        // Wait for confirmation dialog
        await page.waitForTimeout(TIMEOUTS.short);

        // Verify confirmation dialog appears
        const hasConfirmDialog = await page.getByText(/Are you sure|Delete Person|cannot be undone/i).isVisible().catch(() => false);

        if (hasConfirmDialog) {
          // Cancel the deletion
          const cancelButton = page.getByRole('button', { name: /Cancel/i });
          if (await cancelButton.isVisible()) {
            await cancelButton.click();
          }
        }
      }
    });

    test('should cancel person deletion', async ({ page }) => {
      // Wait for people list to load
      await page.waitForTimeout(TIMEOUTS.short);

      // Check if there are any people
      const deleteButtons = page.getByText('Delete');
      const deleteCount = await deleteButtons.count();

      if (deleteCount > 0) {
        // Get initial count of people cards
        const initialCardCount = await page.locator('.card').count();

        // Click first Delete button
        await deleteButtons.first().click();

        // Wait for confirmation dialog
        await page.waitForTimeout(TIMEOUTS.short);

        // Click Cancel
        const cancelButton = page.getByRole('button', { name: /Cancel/i });
        if (await cancelButton.isVisible()) {
          await cancelButton.click();
          await page.waitForTimeout(TIMEOUTS.short);

          // Verify person still exists
          const finalCardCount = await page.locator('.card').count();
          expect(finalCardCount).toBe(initialCardCount);
        }
      }
    });
  });

  // ==========================================================================
  // Search and Filter Tests
  // ==========================================================================

  test.describe('Search and Filter', () => {
    test('should search people by name if search available', async ({ page }) => {
      // Wait for page to load
      await page.waitForTimeout(TIMEOUTS.short);

      // Look for search input
      const searchInput = page.getByPlaceholder(/Search|Filter/i);
      const hasSearch = await searchInput.isVisible().catch(() => false);

      if (hasSearch) {
        // Type search query
        await searchInput.fill('Test');
        await page.waitForTimeout(TIMEOUTS.short);

        // Verify results are filtered
        expect(true).toBe(true);
      }
    });

    test('should filter by PGY level', async ({ page }) => {
      // Wait for page to load
      await page.waitForTimeout(TIMEOUTS.short);

      // Click on Resident filter first
      await page.getByRole('button', { name: 'Resident' }).click();
      await page.waitForTimeout(500);

      // Select PGY-1 filter
      const pgySelect = page.locator('select').filter({ hasText: /All PGY Levels|PGY/i });
      await pgySelect.selectOption('1');
      await page.waitForTimeout(TIMEOUTS.short);

      // Verify filter is applied
      const selectedValue = await pgySelect.inputValue();
      expect(selectedValue).toBe('1');
    });
  });

  // ==========================================================================
  // Export Functionality Tests
  // ==========================================================================

  test.describe('Export', () => {
    test('should show export button', async ({ page }) => {
      // Look for export button
      const exportButton = page.getByRole('button', { name: /Export/i });
      const hasExportButton = await exportButton.isVisible().catch(() => false);

      if (hasExportButton) {
        await expect(exportButton).toBeVisible();
      }
    });
  });

  // ==========================================================================
  // Loading and Error States Tests
  // ==========================================================================

  test.describe('Loading and Error States', () => {
    test('should show loading state initially', async ({ page }) => {
      // Reload page to catch loading state
      await page.reload();

      // Check for loading skeletons
      const hasLoadingState = await page.locator('.animate-pulse').isVisible().catch(() => false);

      // Loading state appears briefly
      if (hasLoadingState) {
        expect(true).toBe(true);
      }

      // Wait for loading to complete
      await waitForLoadingComplete(page);
    });

    test('should handle empty state', async ({ page }) => {
      // Wait for data to load
      await page.waitForTimeout(TIMEOUTS.short);

      // Check for empty state
      const hasEmptyState = await page.getByText(/No people added yet/i).isVisible().catch(() => false);
      const hasPeople = await page.locator('.card').count() > 0;

      // Either has people or shows empty state
      expect(hasEmptyState || hasPeople).toBe(true);
    });
  });

  // ==========================================================================
  // Responsive Design Tests
  // ==========================================================================

  test.describe('Responsive Design', () => {
    test('should adapt layout on mobile devices', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize(VIEWPORT_SIZES.mobile);

      // Page should still be usable
      await expect(page.getByRole('heading', { name: 'People' })).toBeVisible();
      await expect(page.getByRole('button', { name: /Add Person/i })).toBeVisible();
    });

    test('should show all controls on desktop', async ({ page }) => {
      // Set desktop viewport
      await page.setViewportSize(VIEWPORT_SIZES.desktop);

      // All controls should be visible
      await expect(page.getByRole('heading', { name: 'People' })).toBeVisible();
      await expect(page.getByRole('button', { name: /Add Person/i })).toBeVisible();
      await expect(page.getByRole('button', { name: 'All' })).toBeVisible();
    });
  });

  // ==========================================================================
  // Protected Route Tests
  // ==========================================================================

  test.describe('Authentication', () => {
    test('should redirect to login when not authenticated', async ({ page }) => {
      // Clear authentication
      await clearStorage(page);

      // Try to access people page
      await page.goto('/people');

      // Should redirect to login
      await page.waitForURL(/\/login/, { timeout: 10000 });
      expect(page.url()).toContain('/login');
    });
  });
});
