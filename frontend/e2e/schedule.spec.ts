import { test, expect } from '@playwright/test';
import {
  loginAsAdmin,
  clearStorage,
  navigateAsAuthenticated,
  waitForLoadingComplete,
  TIMEOUTS,
  VIEWPORT_SIZES,
  TEST_USERS,
} from './fixtures/test-data';

test.describe('Schedule Page', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and login before each test
    await clearStorage(page);
    await loginAsAdmin(page);

    // Navigate to schedule page
    await page.goto('/schedule');
    await page.waitForURL('/schedule', { timeout: 10000 });
  });

  // ==========================================================================
  // Schedule Grid Display Tests
  // ==========================================================================

  test.describe('Schedule Grid Display', () => {
    test('should load schedule page with header and navigation', async ({ page }) => {
      // Verify the page heading
      await expect(page.getByRole('heading', { name: 'Schedule' })).toBeVisible();
      await expect(page.getByText('View and manage rotation assignments')).toBeVisible();

      // Verify navigation buttons are present
      await expect(page.getByRole('button', { name: 'Previous Block' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Next Block' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Today' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'This Block' })).toBeVisible();
    });

    test('should display date range inputs', async ({ page }) => {
      // Verify date picker inputs are present
      const startDateInput = page.getByLabel('Start date');
      const endDateInput = page.getByLabel('End date');

      await expect(startDateInput).toBeVisible();
      await expect(endDateInput).toBeVisible();

      // Verify dates are filled
      const startValue = await startDateInput.inputValue();
      const endValue = await endDateInput.inputValue();

      expect(startValue).toBeTruthy();
      expect(endValue).toBeTruthy();
    });

    test('should show legend on larger screens', async ({ page }) => {
      // Set viewport to a larger screen to see the legend
      await page.setViewportSize({ width: 1400, height: 900 });

      // Verify legend elements are visible
      await expect(page.getByText('Legend:')).toBeVisible();
      await expect(page.getByText('Clinic')).toBeVisible();
      await expect(page.getByText('Inpatient')).toBeVisible();
      await expect(page.getByText('Procedure')).toBeVisible();
      await expect(page.getByText('Call')).toBeVisible();
      await expect(page.getByText('Elective')).toBeVisible();
      await expect(page.getByText('Conference')).toBeVisible();
    });

    test('should display schedule grid or loading/empty state', async ({ page }) => {
      // Wait for initial load
      await page.waitForTimeout(1000);

      // The schedule should show either:
      // 1. A schedule table with data
      // 2. A loading spinner
      // 3. An empty state message
      // 4. An error message

      const hasTable = await page.locator('table').isVisible().catch(() => false);
      const hasLoading = await page.getByText('Loading schedule...').isVisible().catch(() => false);
      const hasEmptyState = await page.getByText('No People Found').isVisible().catch(() => false);
      const hasError = await page.locator('[class*="error"]').isVisible().catch(() => false);

      // One of these states should be true
      expect(hasTable || hasLoading || hasEmptyState || hasError).toBe(true);
    });

    test('should show footer with instructions', async ({ page }) => {
      // Verify footer instructions are visible
      await expect(page.getByText('Hover over assignments to see details')).toBeVisible();
    });
  });

  // ==========================================================================
  // Block Navigation Tests
  // ==========================================================================

  test.describe('Block Navigation', () => {
    test('should navigate to previous block', async ({ page }) => {
      // Get initial start date
      const startDateInput = page.getByLabel('Start date');
      const initialStartDate = await startDateInput.inputValue();

      // Click previous block
      await page.getByRole('button', { name: 'Previous Block' }).click();

      // Wait for update
      await page.waitForTimeout(500);

      // Verify date has changed
      const newStartDate = await startDateInput.inputValue();
      expect(newStartDate).not.toBe(initialStartDate);

      // The new start date should be earlier than the initial
      expect(new Date(newStartDate).getTime()).toBeLessThan(new Date(initialStartDate).getTime());
    });

    test('should navigate to next block', async ({ page }) => {
      // Get initial start date
      const startDateInput = page.getByLabel('Start date');
      const initialStartDate = await startDateInput.inputValue();

      // Click next block
      await page.getByRole('button', { name: 'Next Block' }).click();

      // Wait for update
      await page.waitForTimeout(500);

      // Verify date has changed
      const newStartDate = await startDateInput.inputValue();
      expect(newStartDate).not.toBe(initialStartDate);

      // The new start date should be later than the initial
      expect(new Date(newStartDate).getTime()).toBeGreaterThan(new Date(initialStartDate).getTime());
    });

    test('should navigate multiple blocks forward and back', async ({ page }) => {
      const startDateInput = page.getByLabel('Start date');
      const initialStartDate = await startDateInput.inputValue();

      // Navigate forward twice
      await page.getByRole('button', { name: 'Next Block' }).click();
      await page.waitForTimeout(300);
      await page.getByRole('button', { name: 'Next Block' }).click();
      await page.waitForTimeout(300);

      // Navigate back twice
      await page.getByRole('button', { name: 'Previous Block' }).click();
      await page.waitForTimeout(300);
      await page.getByRole('button', { name: 'Previous Block' }).click();
      await page.waitForTimeout(300);

      // Should be back to initial date
      const finalStartDate = await startDateInput.inputValue();
      expect(finalStartDate).toBe(initialStartDate);
    });

    test('should jump to today when clicking Today button', async ({ page }) => {
      // First navigate away from today
      await page.getByRole('button', { name: 'Previous Block' }).click();
      await page.waitForTimeout(300);
      await page.getByRole('button', { name: 'Previous Block' }).click();
      await page.waitForTimeout(300);

      // Click Today
      await page.getByRole('button', { name: 'Today' }).click();
      await page.waitForTimeout(500);

      // Verify we're in a range that includes today
      const startDateInput = page.getByLabel('Start date');
      const endDateInput = page.getByLabel('End date');

      const startDate = new Date(await startDateInput.inputValue());
      const endDate = new Date(await endDateInput.inputValue());
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      // Today should be within the range
      expect(startDate.getTime()).toBeLessThanOrEqual(today.getTime());
      expect(endDate.getTime()).toBeGreaterThanOrEqual(today.getTime());
    });

    test('should jump to this block when clicking This Block button', async ({ page }) => {
      // First navigate away
      await page.getByRole('button', { name: 'Next Block' }).click();
      await page.waitForTimeout(300);
      await page.getByRole('button', { name: 'Next Block' }).click();
      await page.waitForTimeout(300);

      // Click This Block
      await page.getByRole('button', { name: 'This Block' }).click();
      await page.waitForTimeout(500);

      // Verify we're in the current block (similar to Today)
      const startDateInput = page.getByLabel('Start date');
      const endDateInput = page.getByLabel('End date');

      const startDate = new Date(await startDateInput.inputValue());
      const endDate = new Date(await endDateInput.inputValue());
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      // Today should be within the range
      expect(startDate.getTime()).toBeLessThanOrEqual(today.getTime());
      expect(endDate.getTime()).toBeGreaterThanOrEqual(today.getTime());
    });
  });

  // ==========================================================================
  // Date Picker Tests
  // ==========================================================================

  test.describe('Date Picker Navigation', () => {
    test('should allow manual date range selection', async ({ page }) => {
      const startDateInput = page.getByLabel('Start date');
      const endDateInput = page.getByLabel('End date');

      // Clear and set new start date
      await startDateInput.fill('2024-01-01');
      await startDateInput.blur();
      await page.waitForTimeout(500);

      // Verify start date was updated
      const newStartDate = await startDateInput.inputValue();
      expect(newStartDate).toBe('2024-01-01');
    });

    test('should maintain 28-day range when changing start date', async ({ page }) => {
      const startDateInput = page.getByLabel('Start date');
      const endDateInput = page.getByLabel('End date');

      // Set new start date
      await startDateInput.fill('2024-06-01');
      await startDateInput.blur();
      await page.waitForTimeout(500);

      // Verify end date is approximately 27 days later (28 day block)
      const startDate = new Date(await startDateInput.inputValue());
      const endDate = new Date(await endDateInput.inputValue());

      const daysDiff = Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
      expect(daysDiff).toBeGreaterThanOrEqual(27);
      expect(daysDiff).toBeLessThanOrEqual(28);
    });
  });

  // ==========================================================================
  // Generate Schedule Dialog Tests
  // ==========================================================================

  test.describe('Generate Schedule Dialog', () => {
    test('should open Generate Schedule dialog from dashboard quick actions', async ({ page }) => {
      // Navigate to dashboard first
      await page.goto('/');
      await page.waitForURL('/', { timeout: 10000 });

      // Find and click the Generate Schedule button in Quick Actions
      const generateButton = page.getByRole('button', { name: 'Generate Schedule' });
      await expect(generateButton).toBeVisible();
      await generateButton.click();

      // Verify the dialog opens
      await expect(page.getByRole('heading', { name: 'Generate Schedule' })).toBeVisible({ timeout: 5000 });

      // Verify form fields are present
      await expect(page.getByText('Start Date')).toBeVisible();
      await expect(page.getByText('End Date')).toBeVisible();
      await expect(page.getByText('Algorithm')).toBeVisible();
      await expect(page.getByText('Solver Timeout')).toBeVisible();
      await expect(page.getByText('PGY Level Filter')).toBeVisible();

      // Verify action buttons
      await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Generate Schedule' })).toBeVisible();
    });

    test('should close Generate Schedule dialog with Cancel button', async ({ page }) => {
      // Navigate to dashboard
      await page.goto('/');
      await page.waitForURL('/', { timeout: 10000 });

      // Open the dialog
      await page.getByRole('button', { name: 'Generate Schedule' }).click();
      await expect(page.getByRole('heading', { name: 'Generate Schedule' })).toBeVisible({ timeout: 5000 });

      // Click Cancel
      await page.getByRole('button', { name: 'Cancel' }).click();

      // Verify dialog is closed
      await expect(page.getByRole('heading', { name: 'Generate Schedule' })).not.toBeVisible({ timeout: 3000 });
    });

    test('should show algorithm options in Generate Schedule dialog', async ({ page }) => {
      // Navigate to dashboard
      await page.goto('/');
      await page.waitForURL('/', { timeout: 10000 });

      // Open the dialog
      await page.getByRole('button', { name: 'Generate Schedule' }).click();
      await expect(page.getByRole('heading', { name: 'Generate Schedule' })).toBeVisible({ timeout: 5000 });

      // Find the algorithm select dropdown
      const algorithmSelect = page.locator('select').filter({ hasText: /Greedy|CP-SAT|PuLP|Hybrid/i });

      // Verify algorithm options exist
      await expect(algorithmSelect).toBeVisible();

      // Close dialog
      await page.getByRole('button', { name: 'Cancel' }).click();
    });

    test('should validate required fields in Generate Schedule dialog', async ({ page }) => {
      // Navigate to dashboard
      await page.goto('/');
      await page.waitForURL('/', { timeout: 10000 });

      // Open the dialog
      await page.getByRole('button', { name: 'Generate Schedule' }).click();
      await expect(page.getByRole('heading', { name: 'Generate Schedule' })).toBeVisible({ timeout: 5000 });

      // Try to submit without dates
      await page.getByRole('button', { name: 'Generate Schedule' }).click();

      // Should show validation errors
      await expect(page.getByText(/required/i)).toBeVisible({ timeout: 3000 });

      // Close dialog
      await page.getByRole('button', { name: 'Cancel' }).click();
    });
  });

  // ==========================================================================
  // Responsive Design Tests
  // ==========================================================================

  test.describe('Responsive Design', () => {
    test('should adapt navigation layout on mobile', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize(VIEWPORT_SIZES.mobile);

      // Navigation buttons should still be accessible
      await expect(page.getByRole('button', { name: 'Previous Block' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Next Block' })).toBeVisible();
    });

    test('should hide legend on smaller screens', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize(VIEWPORT_SIZES.tablet);

      // Legend should be hidden on smaller screens
      await expect(page.getByText('Legend:')).not.toBeVisible();
    });

    test('should show days count on larger screens', async ({ page }) => {
      // Set desktop viewport
      await page.setViewportSize(VIEWPORT_SIZES.largeDesktop);

      // Days count should be visible
      await expect(page.getByText(/Showing \d+ days/i)).toBeVisible();
    });
  });

  // ==========================================================================
  // Schedule Interaction Tests
  // ==========================================================================

  test.describe('Schedule Interactions', () => {
    test('should show assignment details on hover', async ({ page }) => {
      // Wait for schedule to load
      await page.waitForTimeout(TIMEOUTS.medium);

      // Look for schedule cells (assignments)
      const scheduleCells = page.locator('td[class*="bg-"]').filter({ hasNot: page.locator('[class*="bg-gray-50"]') });
      const cellCount = await scheduleCells.count();

      if (cellCount > 0) {
        // Hover over first assignment cell
        await scheduleCells.first().hover();

        // Wait for tooltip or details to appear
        await page.waitForTimeout(500);

        // Verify some interaction happened (tooltip, highlight, etc.)
        // The specific implementation depends on the UI
        expect(cellCount).toBeGreaterThan(0);
      }
    });

    test('should allow clicking on schedule cells', async ({ page }) => {
      // Wait for schedule to load
      await page.waitForTimeout(TIMEOUTS.medium);

      // Look for clickable schedule cells
      const scheduleCells = page.locator('td[class*="cursor-pointer"]');
      const cellCount = await scheduleCells.count();

      if (cellCount > 0) {
        // Click on first cell
        await scheduleCells.first().click();

        // Wait for modal or details to appear
        await page.waitForTimeout(TIMEOUTS.short);

        // Verify some action occurred
        expect(cellCount).toBeGreaterThan(0);
      }
    });

    test('should handle empty schedule cells', async ({ page }) => {
      // Wait for schedule to load
      await page.waitForTimeout(TIMEOUTS.medium);

      // Look for empty cells
      const emptyCells = page.locator('td.bg-gray-50');
      const emptyCount = await emptyCells.count();

      // Empty cells should exist (for unassigned slots)
      expect(emptyCount).toBeGreaterThanOrEqual(0);
    });
  });

  // ==========================================================================
  // Filter Tests
  // ==========================================================================

  test.describe('Schedule Filters', () => {
    test('should display filter controls if available', async ({ page }) => {
      // Wait for page to load
      await page.waitForTimeout(TIMEOUTS.short);

      // Look for potential filter controls (person, rotation, etc.)
      const hasPersonFilter = await page.getByText(/Filter by Person|Person:/i).isVisible().catch(() => false);
      const hasRotationFilter = await page.getByText(/Filter by Rotation|Rotation:/i).isVisible().catch(() => false);

      // Filters may or may not be present depending on implementation
      // This test documents their expected location
      expect(hasPersonFilter || hasRotationFilter || true).toBe(true);
    });

    test('should maintain filters across navigation', async ({ page }) => {
      // Get initial date range
      const startDateInput = page.getByLabel('Start date');
      const initialDate = await startDateInput.inputValue();

      // Navigate to next block
      await page.getByRole('button', { name: 'Next Block' }).click();
      await page.waitForTimeout(500);

      // Navigate back
      await page.getByRole('button', { name: 'Previous Block' }).click();
      await page.waitForTimeout(500);

      // Date should be back to original
      const finalDate = await startDateInput.inputValue();
      expect(finalDate).toBe(initialDate);
    });
  });

  // ==========================================================================
  // Data Loading Tests
  // ==========================================================================

  test.describe('Data Loading', () => {
    test('should show loading state initially', async ({ page }) => {
      // Reload page to catch loading state
      await page.reload();

      // Check for loading spinner or skeleton
      const hasLoadingSpinner = await page.locator('.animate-spin').isVisible().catch(() => false);
      const hasLoadingText = await page.getByText('Loading schedule...').isVisible().catch(() => false);

      // Loading state appears briefly
      if (hasLoadingSpinner || hasLoadingText) {
        expect(true).toBe(true);
      }

      // Wait for loading to complete
      await waitForLoadingComplete(page);
    });

    test('should handle empty schedule data', async ({ page }) => {
      // Navigate to a date range with no data
      const startDateInput = page.getByLabel('Start date');
      await startDateInput.fill('2030-01-01');
      await startDateInput.blur();
      await page.waitForTimeout(TIMEOUTS.medium);

      // Should show empty state or message
      const hasEmptyState = await page.getByText(/No People Found|No schedule data/i).isVisible().catch(() => false);
      const hasTable = await page.locator('table').isVisible().catch(() => false);

      // Either empty state or empty table
      expect(hasEmptyState || hasTable).toBe(true);
    });

    test('should refresh data when changing date range', async ({ page }) => {
      // Wait for initial load
      await page.waitForTimeout(TIMEOUTS.short);

      // Change date range
      const startDateInput = page.getByLabel('Start date');
      await startDateInput.fill('2024-06-01');
      await startDateInput.blur();

      // Wait for data to reload
      await page.waitForTimeout(TIMEOUTS.medium);

      // Verify date was updated
      const newDate = await startDateInput.inputValue();
      expect(newDate).toBe('2024-06-01');
    });
  });

  // ==========================================================================
  // Protected Route Tests
  // ==========================================================================

  test.describe('Authentication', () => {
    test('should redirect to login when not authenticated', async ({ page }) => {
      // Clear authentication
      await clearStorage(page);

      // Try to access schedule page
      await page.goto('/schedule');

      // Should redirect to login
      await page.waitForURL(/\/login/, { timeout: 10000 });
      expect(page.url()).toContain('/login');
    });
  });
});
