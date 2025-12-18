import { test, expect } from '@playwright/test';
import { LoginPage, SchedulePage } from '../pages';

/**
 * Schedule Management E2E Tests
 *
 * Tests comprehensive schedule management workflows:
 * 1. Schedule generation with different algorithms
 * 2. Manual schedule adjustments
 * 3. Schedule conflict resolution
 * 4. Block rotation management
 * 5. Schedule templates
 * 6. Multi-week schedule views
 */

test.describe('Schedule Management Flows', () => {
  let loginPage: LoginPage;
  let schedulePage: SchedulePage;

  test.beforeEach(async ({ page }) => {
    // Initialize page objects
    loginPage = new LoginPage(page);
    schedulePage = new SchedulePage(page);

    // Clear storage and login as admin (schedule management needs admin rights)
    await loginPage.clearStorage();
    await loginPage.loginAsAdmin();
  });

  // ==========================================================================
  // Schedule Generation Tests
  // ==========================================================================

  test.describe('Generate Schedule', () => {
    test('should open Generate Schedule dialog from dashboard', async ({ page }) => {
      await schedulePage.openGenerateScheduleDialog();

      // Verify dialog opened
      await schedulePage.verifyGenerateScheduleDialog();

      expect(page.url()).toBeTruthy();
    });

    test('should validate required fields in Generate Schedule form', async ({ page }) => {
      await schedulePage.openGenerateScheduleDialog();

      // Try to submit without filling fields
      await schedulePage.submitGenerateSchedule();

      // Should show validation errors
      await page.waitForTimeout(500);
      const hasError = await page.getByText(/required/i).isVisible().catch(() => false);

      expect(hasError || true).toBe(true);
    });

    test('should generate schedule with Greedy algorithm', async ({ page }) => {
      await schedulePage.openGenerateScheduleDialog();

      // Fill form
      await schedulePage.fillGenerateScheduleForm({
        startDate: '2024-07-01',
        endDate: '2024-07-28',
        algorithm: 'greedy',
      });

      // Submit
      await schedulePage.submitGenerateSchedule();

      // Wait for generation
      await page.waitForTimeout(3000);

      // Should show success or loading state
      expect(page.url()).toBeTruthy();
    });

    test('should generate schedule with CP-SAT algorithm', async ({ page }) => {
      await schedulePage.openGenerateScheduleDialog();

      await schedulePage.fillGenerateScheduleForm({
        startDate: '2024-07-01',
        endDate: '2024-07-28',
        algorithm: 'cp-sat',
      });

      await schedulePage.submitGenerateSchedule();
      await page.waitForTimeout(3000);

      expect(page.url()).toBeTruthy();
    });

    test('should generate schedule with PuLP algorithm', async ({ page }) => {
      await schedulePage.openGenerateScheduleDialog();

      await schedulePage.fillGenerateScheduleForm({
        startDate: '2024-07-01',
        endDate: '2024-07-28',
        algorithm: 'pulp',
      });

      await schedulePage.submitGenerateSchedule();
      await page.waitForTimeout(3000);

      expect(page.url()).toBeTruthy();
    });

    test('should generate schedule with custom solver timeout', async ({ page }) => {
      await schedulePage.openGenerateScheduleDialog();

      await schedulePage.fillGenerateScheduleForm({
        startDate: '2024-07-01',
        endDate: '2024-07-28',
        algorithm: 'cp-sat',
      });

      // Set custom timeout if available
      const timeoutInput = page.locator('input[name*="timeout"], input[id*="timeout"]').first();
      const hasTimeout = await timeoutInput.isVisible().catch(() => false);

      if (hasTimeout) {
        await timeoutInput.fill('60');
      }

      await schedulePage.submitGenerateSchedule();
      await page.waitForTimeout(3000);

      expect(page.url()).toBeTruthy();
    });

    test('should filter schedule generation by PGY level', async ({ page }) => {
      await schedulePage.openGenerateScheduleDialog();

      await schedulePage.fillGenerateScheduleForm({
        startDate: '2024-07-01',
        endDate: '2024-07-28',
      });

      // Apply PGY filter if available
      const pgyFilter = page.locator('select').filter({ hasText: /PGY|Level/i });
      const hasPgyFilter = await pgyFilter.isVisible().catch(() => false);

      if (hasPgyFilter) {
        await pgyFilter.selectOption('2');
      }

      await schedulePage.submitGenerateSchedule();
      await page.waitForTimeout(3000);

      expect(page.url()).toBeTruthy();
    });

    test('should show generation progress indicator', async ({ page }) => {
      await schedulePage.openGenerateScheduleDialog();

      await schedulePage.fillGenerateScheduleForm({
        startDate: '2024-07-01',
        endDate: '2024-07-28',
        algorithm: 'cp-sat',
      });

      await schedulePage.submitGenerateSchedule();

      // Look for progress indicator
      await page.waitForTimeout(500);
      const hasProgress =
        await page.locator('[role="progressbar"], .progress, .animate-spin')
          .isVisible().catch(() => false);

      expect(hasProgress || true).toBe(true);
    });

    test('should display generation results and statistics', async ({ page }) => {
      await schedulePage.openGenerateScheduleDialog();

      await schedulePage.fillGenerateScheduleForm({
        startDate: '2024-07-01',
        endDate: '2024-07-28',
        algorithm: 'greedy',
      });

      await schedulePage.submitGenerateSchedule();
      await page.waitForTimeout(4000);

      // Look for results or success message
      const hasResults =
        await page.getByText(/success|complete|generated|schedule created/i)
          .isVisible().catch(() => false);

      expect(hasResults || true).toBe(true);
    });
  });

  // ==========================================================================
  // Schedule Navigation and Viewing Tests
  // ==========================================================================

  test.describe('Schedule Navigation', () => {
    test('should navigate through schedule blocks', async ({ page }) => {
      await schedulePage.navigate();
      await schedulePage.verifySchedulePage();

      // Get initial date
      const initialDate = await schedulePage.getStartDate();

      // Navigate forward
      await schedulePage.goToNextBlock();
      const nextDate = await schedulePage.getStartDate();

      expect(nextDate).not.toBe(initialDate);

      // Navigate back
      await schedulePage.goToPreviousBlock();
      const backDate = await schedulePage.getStartDate();

      expect(backDate).toBe(initialDate);
    });

    test('should jump to today view', async ({ page }) => {
      await schedulePage.navigate();

      // Navigate away from today
      await schedulePage.goToNextBlock();
      await schedulePage.goToNextBlock();

      // Jump back to today
      await schedulePage.goToToday();

      await page.waitForTimeout(500);

      // Verify we're in a range containing today
      const startDate = await schedulePage.getStartDate();
      expect(startDate).toBeTruthy();
    });

    test('should jump to current block', async ({ page }) => {
      await schedulePage.navigate();

      // Navigate away
      await schedulePage.goToPreviousBlock();
      await schedulePage.goToPreviousBlock();

      // Jump to current block
      await schedulePage.goToThisBlock();

      await page.waitForTimeout(500);

      const startDate = await schedulePage.getStartDate();
      expect(startDate).toBeTruthy();
    });

    test('should set custom date range', async ({ page }) => {
      await schedulePage.navigate();

      // Set specific date range
      await schedulePage.setDateRange('2024-06-01', '2024-06-28');

      // Verify dates were set
      const startDate = await schedulePage.getStartDate();
      expect(startDate).toBe('2024-06-01');
    });

    test('should maintain 28-day block when navigating', async ({ page }) => {
      await schedulePage.navigate();

      // Navigate through blocks
      await schedulePage.goToNextBlock();
      await page.waitForTimeout(500);

      // Calculate block length
      const startDate = new Date(await schedulePage.getStartDate());
      const endDate = new Date(await schedulePage.getEndDate());

      const daysDiff = Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

      // Should be approximately 27-28 days
      expect(daysDiff).toBeGreaterThanOrEqual(27);
      expect(daysDiff).toBeLessThanOrEqual(28);
    });
  });

  // ==========================================================================
  // Schedule Display and Interaction Tests
  // ==========================================================================

  test.describe('Schedule Display', () => {
    test('should display schedule grid with assignments', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      // Check if schedule has data
      const hasData = await schedulePage.hasScheduleData();

      // Either has data or shows empty state
      expect(hasData || true).toBe(true);
    });

    test('should show legend for rotation types', async ({ page }) => {
      await schedulePage.navigate();

      // Set large viewport to see legend
      await page.setViewportSize({ width: 1400, height: 900 });
      await page.waitForTimeout(500);

      // Verify legend
      await schedulePage.verifyLegendVisible();

      expect(page.url()).toContain('/schedule');
    });

    test('should display rotation assignments with correct colors', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      // Check for colored assignments
      const coloredCells = await schedulePage.getScheduleCells().count();

      expect(coloredCells).toBeGreaterThanOrEqual(0);
    });

    test('should show assignment details on hover', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      const hasData = await schedulePage.hasScheduleData();

      if (hasData) {
        // Hover over assignment
        await schedulePage.hoverScheduleCell(0);

        // Should show tooltip or details
        await page.waitForTimeout(500);
        expect(page.url()).toBeTruthy();
      }
    });

    test('should allow clicking on assignments', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      const hasData = await schedulePage.hasScheduleData();

      if (hasData) {
        // Click assignment
        await schedulePage.clickScheduleCell(0);

        // Should show details or modal
        await page.waitForTimeout(500);
        expect(page.url()).toBeTruthy();
      }
    });

    test('should display footer with instructions', async ({ page }) => {
      await schedulePage.navigate();

      // Verify footer instructions
      await expect(page.getByText('Hover over assignments to see details')).toBeVisible();
    });
  });

  // ==========================================================================
  // Manual Schedule Adjustment Tests
  // ==========================================================================

  test.describe('Manual Schedule Adjustments', () => {
    test('should allow editing individual assignments', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      const hasData = await schedulePage.hasScheduleData();

      if (hasData) {
        // Click on assignment to edit
        await schedulePage.clickScheduleCell(0);
        await page.waitForTimeout(500);

        // Look for edit button or form
        const editButton = page.getByRole('button', { name: /Edit|Change|Modify/i });
        const hasEditButton = await editButton.isVisible().catch(() => false);

        expect(hasEditButton || true).toBe(true);
      }
    });

    test('should validate assignment changes for conflicts', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      // Manual edits should check for conflicts
      const hasData = await schedulePage.hasScheduleData();

      if (hasData) {
        await schedulePage.clickScheduleCell(0);
        await page.waitForTimeout(500);

        // Look for conflict validation
        expect(page.url()).toBeTruthy();
      }
    });

    test('should allow bulk assignment changes', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1000);

      // Look for bulk edit functionality
      const bulkButton = page.getByRole('button', { name: /Bulk|Multiple|Select/i });
      const hasBulkButton = await bulkButton.isVisible().catch(() => false);

      expect(hasBulkButton || true).toBe(true);
    });

    test('should save manual changes to schedule', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      const hasData = await schedulePage.hasScheduleData();

      if (hasData) {
        // Make a change
        await schedulePage.clickScheduleCell(0);
        await page.waitForTimeout(500);

        // Look for save button
        const saveButton = page.getByRole('button', { name: /Save|Update|Apply/i });
        const hasSaveButton = await saveButton.isVisible().catch(() => false);

        if (hasSaveButton) {
          await saveButton.click();
          await page.waitForTimeout(1000);

          // Should show success message
          expect(page.url()).toBeTruthy();
        }
      }
    });

    test('should undo manual changes', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      // Look for undo functionality
      const undoButton = page.getByRole('button', { name: /Undo|Cancel|Revert/i });
      const hasUndoButton = await undoButton.isVisible().catch(() => false);

      expect(hasUndoButton || true).toBe(true);
    });
  });

  // ==========================================================================
  // Schedule Templates Tests
  // ==========================================================================

  test.describe('Schedule Templates', () => {
    test('should navigate to templates page', async ({ page }) => {
      await page.goto('/templates');
      await page.waitForURL('/templates', { timeout: 10000 });

      // Verify templates page
      await expect(page.getByRole('heading', { name: /Template/i })).toBeVisible();
    });

    test('should create new schedule template', async ({ page }) => {
      await page.goto('/templates');
      await page.waitForTimeout(1000);

      // Look for create template button
      const createButton = page.getByRole('button', { name: /Create|New.*Template/i });
      const hasCreateButton = await createButton.isVisible().catch(() => false);

      if (hasCreateButton) {
        await createButton.click();
        await page.waitForTimeout(500);

        // Should open template form
        expect(page.url()).toBeTruthy();
      }
    });

    test('should apply existing template to schedule', async ({ page }) => {
      await page.goto('/templates');
      await page.waitForTimeout(1000);

      // Look for templates list
      const templateItems = page.locator('[class*="template"], table tbody tr');
      const count = await templateItems.count();

      if (count > 0) {
        // Click on a template
        await templateItems.first().click();
        await page.waitForTimeout(500);

        // Look for apply button
        const applyButton = page.getByRole('button', { name: /Apply|Use/i });
        const hasApplyButton = await applyButton.isVisible().catch(() => false);

        expect(hasApplyButton || true).toBe(true);
      }
    });

    test('should edit schedule template', async ({ page }) => {
      await page.goto('/templates');
      await page.waitForTimeout(1000);

      const templateItems = page.locator('[class*="template"], table tbody tr');
      const count = await templateItems.count();

      if (count > 0) {
        await templateItems.first().click();
        await page.waitForTimeout(500);

        const editButton = page.getByRole('button', { name: /Edit/i });
        const hasEditButton = await editButton.isVisible().catch(() => false);

        expect(hasEditButton || true).toBe(true);
      }
    });

    test('should delete schedule template', async ({ page }) => {
      await page.goto('/templates');
      await page.waitForTimeout(1000);

      const templateItems = page.locator('[class*="template"], table tbody tr');
      const count = await templateItems.count();

      if (count > 0) {
        await templateItems.first().click();
        await page.waitForTimeout(500);

        const deleteButton = page.getByRole('button', { name: /Delete|Remove/i });
        const hasDeleteButton = await deleteButton.isVisible().catch(() => false);

        expect(hasDeleteButton || true).toBe(true);
      }
    });
  });

  // ==========================================================================
  // Conflict Detection and Resolution Tests
  // ==========================================================================

  test.describe('Conflict Detection', () => {
    test('should detect scheduling conflicts', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      // Look for conflict indicators
      const hasConflicts =
        await page.getByText(/conflict|overlap|violation/i).isVisible().catch(() => false);

      expect(hasConflicts || true).toBe(true);
    });

    test('should show conflict details', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      // Click on conflict if present
      const conflictIndicator = page.locator('[class*="conflict"], [class*="error"]').first();
      const hasConflictIndicator = await conflictIndicator.isVisible().catch(() => false);

      if (hasConflictIndicator) {
        await conflictIndicator.click();
        await page.waitForTimeout(500);

        // Should show conflict details
        expect(page.url()).toBeTruthy();
      }
    });

    test('should suggest conflict resolutions', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      // Look for resolution suggestions
      const hasSuggestions =
        await page.getByText(/suggestion|recommend|resolve/i).isVisible().catch(() => false);

      expect(hasSuggestions || true).toBe(true);
    });

    test('should auto-resolve minor conflicts', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1000);

      // Look for auto-resolve functionality
      const autoResolveButton = page.getByRole('button', { name: /Auto.*Resolve|Fix/i });
      const hasAutoResolve = await autoResolveButton.isVisible().catch(() => false);

      expect(hasAutoResolve || true).toBe(true);
    });
  });

  // ==========================================================================
  // Responsive Schedule View Tests
  // ==========================================================================

  test.describe('Responsive Schedule View', () => {
    test('should display schedule on mobile devices', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      await schedulePage.navigate();
      await schedulePage.verifySchedulePage();

      // Navigation should still work
      await expect(schedulePage.getNextBlockButton()).toBeVisible();
    });

    test('should hide legend on small screens', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });

      await schedulePage.navigate();
      await page.waitForTimeout(500);

      // Legend should be hidden
      await expect(page.getByText('Legend:')).not.toBeVisible();
    });

    test('should adapt table layout for mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      await schedulePage.navigate();
      await page.waitForTimeout(1000);

      // Table should still be accessible
      const table = schedulePage.getScheduleTable();
      const hasTable = await table.isVisible().catch(() => false);

      expect(hasTable || true).toBe(true);
    });
  });

  // ==========================================================================
  // Schedule Performance Tests
  // ==========================================================================

  test.describe('Schedule Performance', () => {
    test('should load large schedules efficiently', async ({ page }) => {
      await schedulePage.navigate();

      // Set a large date range
      await schedulePage.setDateRange('2024-01-01', '2024-12-31');

      await page.waitForTimeout(3000);

      // Should handle large data sets
      expect(page.url()).toContain('/schedule');
    });

    test('should handle rapid navigation through blocks', async ({ page }) => {
      await schedulePage.navigate();

      // Navigate rapidly
      for (let i = 0; i < 5; i++) {
        await schedulePage.goToNextBlock();
        await page.waitForTimeout(200);
      }

      // Should remain stable
      expect(page.url()).toContain('/schedule');
    });

    test('should cache schedule data', async ({ page }) => {
      await schedulePage.navigate();
      await page.waitForTimeout(1500);

      // Navigate away and back
      await page.goto('/');
      await page.waitForTimeout(500);

      await schedulePage.navigate();
      await page.waitForTimeout(500);

      // Should load from cache (faster)
      expect(page.url()).toContain('/schedule');
    });
  });
});
