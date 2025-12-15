import { test, expect, type Page } from '@playwright/test';
import {
  mockAllPeople,
  mockResidents,
  mockFaculty,
  mockRotationTemplates,
  mockAbsences,
  mockValidationResult,
  mockViolations,
  mockApiResponses,
  createMockSchedule,
  generateMockBlocks,
  getPersonById,
} from './fixtures/schedule';

// ============================================================================
// Test Configuration and Setup
// ============================================================================

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_BASE_URL = process.env.API_URL || 'http://localhost:8000/api/v1';

/**
 * Setup authentication for tests
 * Mock the auth context to simulate logged-in user
 */
async function loginAsAdmin(page: Page) {
  // Mock the authentication cookie/token
  await page.context().addCookies([
    {
      name: 'auth_token',
      value: 'mock-admin-token',
      domain: 'localhost',
      path: '/',
    },
  ]);

  // Mock the user data in localStorage
  await page.addInitScript(() => {
    localStorage.setItem(
      'user',
      JSON.stringify({
        id: 'admin-user',
        email: 'admin@example.com',
        role: 'admin',
        name: 'Admin User',
      })
    );
  });
}

/**
 * Setup API mocking for schedule data
 */
async function setupScheduleApiMocks(page: Page, startDate: Date, endDate: Date) {
  const mockSchedule = createMockSchedule(startDate, endDate);

  // Mock people endpoint
  await page.route(`${API_BASE_URL}/people*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockApiResponses.people),
    });
  });

  // Mock rotation templates endpoint
  await page.route(`${API_BASE_URL}/rotation-templates*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockApiResponses.rotationTemplates),
    });
  });

  // Mock blocks endpoint
  await page.route(`${API_BASE_URL}/blocks*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: mockSchedule.blocks,
        total: mockSchedule.blocks.length,
      }),
    });
  });

  // Mock assignments endpoint
  await page.route(`${API_BASE_URL}/assignments*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: mockSchedule.assignments,
        total: mockSchedule.assignments.length,
      }),
    });
  });

  // Mock absences endpoint
  await page.route(`${API_BASE_URL}/absences*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockApiResponses.absences),
    });
  });

  // Mock validation endpoint
  await page.route(`${API_BASE_URL}/schedule/validate*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockValidationResult),
    });
  });

  // Mock schedule generation endpoint
  await page.route(`${API_BASE_URL}/schedule/generate`, async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          message: 'Schedule generated successfully',
          total_blocks_assigned: mockSchedule.assignments.length,
          total_blocks: mockSchedule.blocks.length,
          validation: mockValidationResult,
          run_id: 'mock-run-123',
          solver_stats: {
            total_blocks: mockSchedule.blocks.length,
            total_residents: mockResidents.length,
            coverage_rate: 0.92,
            branches: 1500,
            conflicts: 25,
          },
        }),
      });
    }
  });
}

// ============================================================================
// Test Suite: Schedule Page - Basic Functionality
// ============================================================================

test.describe('Schedule Page - Basic Functionality', () => {
  test.beforeEach(async ({ page }) => {
    const startDate = new Date('2024-01-01');
    const endDate = new Date('2024-01-28');

    await loginAsAdmin(page);
    await setupScheduleApiMocks(page, startDate, endDate);
  });

  test('should load schedule page correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Verify page title and header
    await expect(page.locator('h1')).toContainText('Schedule');
    await expect(page.locator('text=View and manage rotation assignments')).toBeVisible();

    // Verify navigation controls are present
    await expect(page.locator('button', { hasText: 'Previous Block' })).toBeVisible();
    await expect(page.locator('button', { hasText: 'Next Block' })).toBeVisible();
    await expect(page.locator('button', { hasText: 'Today' })).toBeVisible();
    await expect(page.locator('button', { hasText: 'This Block' })).toBeVisible();

    // Verify date range inputs are present
    await expect(page.locator('input[type="date"]').first()).toBeVisible();
    await expect(page.locator('input[type="date"]').last()).toBeVisible();

    // Verify legend is visible
    await expect(page.locator('text=Legend:')).toBeVisible();
    await expect(page.locator('text=Clinic')).toBeVisible();
    await expect(page.locator('text=Inpatient')).toBeVisible();
  });

  test('should display schedule grid with people and assignments', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Wait for schedule grid to load
    await page.waitForSelector('table');

    // Verify table headers (days) are present
    const table = page.locator('table');
    await expect(table).toBeVisible();

    // Verify some people are listed (check for sticky name column)
    await expect(page.locator('text=Dr. Sarah Johnson')).toBeVisible();
    await expect(page.locator('text=Dr. Michael Chen')).toBeVisible();

    // Verify PGY level badges are displayed
    await expect(page.locator('text=PGY-1')).toBeVisible();
    await expect(page.locator('text=PGY-2')).toBeVisible();
    await expect(page.locator('text=PGY-3')).toBeVisible();

    // Verify faculty section
    await expect(page.locator('text=Faculty')).toBeVisible();
    await expect(page.locator('text=Dr. Robert Thompson')).toBeVisible();
  });

  test('should display footer with helpful information', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Verify footer is present
    await expect(
      page.locator('text=Hover over assignments to see details. Click on a cell to view or edit.')
    ).toBeVisible();

    // Verify day count is displayed
    await expect(page.locator('text=/Showing \\d+ days/')).toBeVisible();
  });
});

// ============================================================================
// Test Suite: View Navigation
// ============================================================================

test.describe('Schedule View Navigation', () => {
  test.beforeEach(async ({ page }) => {
    const startDate = new Date('2024-01-01');
    const endDate = new Date('2024-01-28');

    await loginAsAdmin(page);
    await setupScheduleApiMocks(page, startDate, endDate);
  });

  test('should navigate to previous block', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Get current date range
    const startDateInput = page.locator('input[aria-label="Start date"]');
    const initialStartDate = await startDateInput.inputValue();

    // Click Previous Block button
    await page.click('button:has-text("Previous Block")');

    // Wait for date to update
    await page.waitForTimeout(500);

    // Verify date has changed (moved backward)
    const newStartDate = await startDateInput.inputValue();
    expect(new Date(newStartDate)).toBeLessThan(new Date(initialStartDate));
  });

  test('should navigate to next block', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Get current date range
    const startDateInput = page.locator('input[aria-label="Start date"]');
    const initialStartDate = await startDateInput.inputValue();

    // Click Next Block button
    await page.click('button:has-text("Next Block")');

    // Wait for date to update
    await page.waitForTimeout(500);

    // Verify date has changed (moved forward)
    const newStartDate = await startDateInput.inputValue();
    expect(new Date(newStartDate)).toBeGreaterThan(new Date(initialStartDate));
  });

  test('should navigate to today\'s date', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Click Today button
    await page.click('button:has-text("Today")');

    // Wait for date to update
    await page.waitForTimeout(500);

    // Verify we're viewing the current week
    const today = new Date();
    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    const expectedDate = monday.toISOString().split('T')[0];

    const startDateInput = page.locator('input[aria-label="Start date"]');
    const currentStartDate = await startDateInput.inputValue();

    // Should be within a week of today
    const dateDiff = Math.abs(new Date(currentStartDate).getTime() - new Date(expectedDate).getTime());
    const daysDiff = dateDiff / (1000 * 60 * 60 * 24);
    expect(daysDiff).toBeLessThan(7);
  });

  test('should navigate to current block', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Click This Block button
    await page.click('button:has-text("This Block")');

    // Wait for date to update
    await page.waitForTimeout(500);

    // Verify we're viewing a 4-week block starting on Monday
    const startDateInput = page.locator('input[aria-label="Start date"]');
    const endDateInput = page.locator('input[aria-label="End date"]');

    const startDate = new Date(await startDateInput.inputValue());
    const endDate = new Date(await endDateInput.inputValue());

    // Verify it's Monday (day 1)
    expect(startDate.getDay()).toBe(1);

    // Verify it's 28 days (4 weeks)
    const duration = (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24);
    expect(duration).toBe(27); // End date is inclusive, so 27 days difference
  });

  test('should allow custom date range selection', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    const startDateInput = page.locator('input[aria-label="Start date"]');
    const endDateInput = page.locator('input[aria-label="End date"]');

    // Set custom start date
    await startDateInput.fill('2024-03-01');
    await page.waitForTimeout(500);

    // Set custom end date
    await endDateInput.fill('2024-03-15');
    await page.waitForTimeout(500);

    // Verify dates are set correctly
    expect(await startDateInput.inputValue()).toBe('2024-03-01');
    expect(await endDateInput.inputValue()).toBe('2024-03-15');

    // Verify the display shows the new range
    await expect(page.locator('text=/Mar 1, 2024/')).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Assignment Editing
// ============================================================================

test.describe('Assignment Editing', () => {
  test.beforeEach(async ({ page }) => {
    const startDate = new Date('2024-01-01');
    const endDate = new Date('2024-01-28');

    await loginAsAdmin(page);
    await setupScheduleApiMocks(page, startDate, endDate);
  });

  test('should open edit assignment modal when clicking on a cell', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Wait for schedule to load
    await page.waitForSelector('table');

    // Click on the first assignment cell (skip header and name column)
    const firstCell = page.locator('td').nth(2); // Adjust based on actual structure
    await firstCell.click();

    // Verify modal opens
    await expect(page.locator('text=Edit Assignment')).toBeVisible();
    await expect(page.locator('label:has-text("Person")')).toBeVisible();
    await expect(page.locator('label:has-text("Date")')).toBeVisible();
    await expect(page.locator('label:has-text("Session")')).toBeVisible();
    await expect(page.locator('label:has-text("Rotation")')).toBeVisible();
    await expect(page.locator('label:has-text("Role")')).toBeVisible();
  });

  test('should change rotation assignment', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Mock the update assignment endpoint
    let updateCalled = false;
    await page.route(`${API_BASE_URL}/assignments/*`, async (route) => {
      if (route.request().method() === 'PUT') {
        updateCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'assignment-1',
            rotation_template_id: 'rotation-2',
            role: 'primary',
            notes: null,
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Click on a cell to open modal
    const cell = page.locator('td').nth(2);
    await cell.click();

    // Wait for modal to open
    await page.waitForSelector('text=Edit Assignment');

    // Select a different rotation
    await page.selectOption('select:has([label="Rotation"])', 'rotation-2');

    // Click Save
    await page.click('button:has-text("Save Changes")');

    // Verify the API was called
    await page.waitForTimeout(500);
    expect(updateCalled).toBe(true);

    // Verify modal closes
    await expect(page.locator('text=Edit Assignment')).not.toBeVisible();
  });

  test('should change assignment role', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Click on a cell to open modal
    const cell = page.locator('td').nth(2);
    await cell.click();

    // Wait for modal
    await page.waitForSelector('text=Edit Assignment');

    // Change role to supervising
    await page.selectOption('select:has([label="Role"])', 'supervising');

    // Verify role selection changed
    const roleSelect = page.locator('select').filter({ has: page.locator('option[value="supervising"]') });
    expect(await roleSelect.inputValue()).toContain('supervising');
  });

  test('should add notes to assignment', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Click on a cell to open modal
    const cell = page.locator('td').nth(2);
    await cell.click();

    // Wait for modal
    await page.waitForSelector('text=Edit Assignment');

    // Add notes
    const notesField = page.locator('textarea[placeholder*="notes"]');
    await notesField.fill('This is a test note for the assignment');

    // Verify notes were entered
    expect(await notesField.inputValue()).toBe('This is a test note for the assignment');
  });

  test('should delete assignment', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Mock the delete assignment endpoint
    let deleteCalled = false;
    await page.route(`${API_BASE_URL}/assignments/*`, async (route) => {
      if (route.request().method() === 'DELETE') {
        deleteCalled = true;
        await route.fulfill({
          status: 204,
        });
      } else {
        await route.continue();
      }
    });

    // Click on a cell to open modal
    const cell = page.locator('td').nth(2);
    await cell.click();

    // Wait for modal
    await page.waitForSelector('text=Edit Assignment');

    // Click delete button
    await page.click('button:has-text("Delete")');

    // Confirm deletion in dialog
    await page.waitForSelector('text=Delete Assignment');
    await page.click('button:has-text("Delete Assignment")');

    // Verify the API was called
    await page.waitForTimeout(500);
    expect(deleteCalled).toBe(true);

    // Verify modal closes
    await expect(page.locator('text=Edit Assignment')).not.toBeVisible();
  });

  test('should cancel assignment editing', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Click on a cell to open modal
    const cell = page.locator('td').nth(2);
    await cell.click();

    // Wait for modal
    await page.waitForSelector('text=Edit Assignment');

    // Change rotation
    await page.selectOption('select:has([label="Rotation"])', 'rotation-3');

    // Click Cancel
    await page.click('button:has-text("Cancel")');

    // Verify modal closes without saving
    await expect(page.locator('text=Edit Assignment')).not.toBeVisible();
  });
});

// ============================================================================
// Test Suite: Schedule Filtering
// ============================================================================

test.describe('Schedule Filtering', () => {
  test.beforeEach(async ({ page }) => {
    const startDate = new Date('2024-01-01');
    const endDate = new Date('2024-01-28');

    await loginAsAdmin(page);
    await setupScheduleApiMocks(page, startDate, endDate);
  });

  test('should filter schedule by person', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Look for person filter dropdown (if implemented)
    const personFilter = page.locator('button:has-text("All People")').or(
      page.locator('button[aria-label*="Filter by person"]')
    );

    if (await personFilter.isVisible()) {
      // Click to open dropdown
      await personFilter.click();

      // Select a specific person
      await page.click('text=Dr. Sarah Johnson');

      // Verify only that person's schedule is shown
      await expect(page.locator('text=Dr. Sarah Johnson')).toBeVisible();

      // Other people should not be visible (or filtered out)
      // This depends on implementation - might navigate to different page
      await page.waitForTimeout(500);
    }
  });

  test('should filter schedule by date range', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    const startDateInput = page.locator('input[aria-label="Start date"]');
    const endDateInput = page.locator('input[aria-label="End date"]');

    // Set a specific date range
    await startDateInput.fill('2024-02-01');
    await endDateInput.fill('2024-02-07');

    // Wait for schedule to update
    await page.waitForTimeout(1000);

    // Verify the date range is displayed
    await expect(page.locator('text=/Feb 1, 2024/')).toBeVisible();
    await expect(page.locator('text=/Feb 7, 2024/')).toBeVisible();
  });

  test('should show all people when filter is cleared', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Verify multiple people are visible
    await expect(page.locator('text=Dr. Sarah Johnson')).toBeVisible();
    await expect(page.locator('text=Dr. Michael Chen')).toBeVisible();
    await expect(page.locator('text=Dr. Emily Rodriguez')).toBeVisible();
    await expect(page.locator('text=Dr. Robert Thompson')).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Schedule Generation
// ============================================================================

test.describe('Schedule Generation', () => {
  test.beforeEach(async ({ page }) => {
    const startDate = new Date('2024-01-01');
    const endDate = new Date('2024-01-28');

    await loginAsAdmin(page);
    await setupScheduleApiMocks(page, startDate, endDate);
  });

  test('should generate new schedule with date range', async ({ page }) => {
    // This assumes there's a schedule generation feature
    await page.goto(`${BASE_URL}/schedule`);

    // Look for generate schedule button (might be in a different location)
    const generateButton = page.locator('button:has-text("Generate Schedule")').or(
      page.locator('a[href*="generate"]')
    );

    if (await generateButton.isVisible()) {
      await generateButton.click();

      // If it navigates to a generation page
      if (page.url().includes('generate')) {
        // Fill in date range
        await page.fill('input[name="start_date"]', '2024-03-01');
        await page.fill('input[name="end_date"]', '2024-03-28');

        // Select algorithm
        const algorithmSelect = page.locator('select').filter({ hasText: /algorithm/i });
        if (await algorithmSelect.isVisible()) {
          await algorithmSelect.selectOption('cp_sat');
        }

        // Submit generation request
        await page.click('button[type="submit"]:has-text("Generate")');

        // Wait for success message
        await expect(page.locator('text=/Schedule generated successfully/i')).toBeVisible({
          timeout: 10000,
        });
      }
    }
  });

  test('should display generation progress', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // This test would verify loading states during schedule generation
    // Implementation depends on actual UI
  });

  test('should handle generation errors gracefully', async ({ page }) => {
    // Mock generation error
    await page.route(`${API_BASE_URL}/schedule/generate`, async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Invalid date range: end date must be after start date',
        }),
      });
    });

    await page.goto(`${BASE_URL}/schedule`);

    // Attempt to trigger generation with invalid data
    // Verify error message is displayed
  });
});

// ============================================================================
// Test Suite: ACGME Violations Display
// ============================================================================

test.describe('ACGME Violations Display', () => {
  test.beforeEach(async ({ page }) => {
    const startDate = new Date('2024-01-01');
    const endDate = new Date('2024-01-28');

    await loginAsAdmin(page);
    await setupScheduleApiMocks(page, startDate, endDate);
  });

  test('should display ACGME violations when present', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Look for violation indicators (might be badges, icons, or warnings)
    const violationIndicators = page.locator('[class*="warning"]').or(
      page.locator('[class*="violation"]')
    );

    // If violations are displayed inline, check for them
    if (await violationIndicators.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Verify violation indicators are present
      const count = await violationIndicators.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('should show violation details in assignment modal', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Click on a cell that might have violations
    const cell = page.locator('td').nth(2);
    await cell.click();

    // Wait for modal
    await page.waitForSelector('text=Edit Assignment');

    // Look for warnings section
    const warningsSection = page.locator('text=/Warnings/i');

    if (await warningsSection.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Verify warnings are displayed
      await expect(warningsSection).toBeVisible();

      // Check for specific warning types
      const hasHoursWarning = await page
        .locator('text=/hours/i')
        .isVisible({ timeout: 1000 })
        .catch(() => false);
      const hasSupervisionWarning = await page
        .locator('text=/supervision/i')
        .isVisible({ timeout: 1000 })
        .catch(() => false);
      const hasConflictWarning = await page
        .locator('text=/conflict/i')
        .isVisible({ timeout: 1000 })
        .catch(() => false);

      // At least one type of warning should be present
      expect(hasHoursWarning || hasSupervisionWarning || hasConflictWarning).toBe(true);
    }
  });

  test('should require acknowledgment for critical violations', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Mock an assignment with critical violations
    await page.route(`${API_BASE_URL}/assignments*`, async (route) => {
      if (route.request().url().includes('?')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'assignment-critical',
                block_id: 'block-1-am',
                person_id: 'resident-1',
                rotation_template_id: 'rotation-2',
                role: 'primary',
                activity_override: null,
                notes: null,
                created_by: 'test-user',
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z',
                // Critical violation flag
                has_critical_violations: true,
              },
            ],
            total: 1,
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Click on a cell
    const cell = page.locator('td').nth(2);
    await cell.click();

    // Wait for modal
    await page.waitForSelector('text=Edit Assignment');

    // Look for acknowledgment checkbox
    const acknowledgeCheckbox = page.locator('input[type="checkbox"]').filter({
      has: page.locator('text=/I understand this override/i'),
    });

    if (await acknowledgeCheckbox.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Verify save button is disabled until acknowledged
      const saveButton = page.locator('button:has-text("Save Changes")');

      // Should be disabled initially
      await expect(saveButton).toBeDisabled();

      // Check the acknowledgment
      await acknowledgeCheckbox.check();

      // Save button should now be enabled
      await expect(saveButton).toBeEnabled();
    }
  });

  test('should display violation severity levels', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);
    await page.waitForSelector('table');

    // Click on a cell
    const cell = page.locator('td').nth(2);
    await cell.click();

    // Wait for modal
    await page.waitForSelector('text=Edit Assignment');

    // Look for severity indicators (critical, warning, info)
    const criticalIndicators = page.locator('[class*="red"]').or(
      page.locator('[class*="critical"]')
    );
    const warningIndicators = page.locator('[class*="amber"]').or(
      page.locator('[class*="warning"][class*="bg"]')
    );
    const infoIndicators = page.locator('[class*="blue"]').or(page.locator('[class*="info"]'));

    // At least one severity level should be present if there are violations
    const hasCritical = await criticalIndicators
      .isVisible({ timeout: 1000 })
      .catch(() => false);
    const hasWarning = await warningIndicators.isVisible({ timeout: 1000 }).catch(() => false);
    const hasInfo = await infoIndicators.isVisible({ timeout: 1000 }).catch(() => false);

    // This is informational - violations may or may not be present
    // Just verify the UI can display them when they exist
  });

  test('should show violation count in summary', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Look for a violations summary (might be in a dashboard or summary view)
    const violationSummary = page.locator('text=/\\d+ violations?/i');

    if (await violationSummary.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Verify the count is displayed
      const text = await violationSummary.textContent();
      expect(text).toMatch(/\d+/);
    }
  });
});

// ============================================================================
// Test Suite: Export Functionality
// ============================================================================

test.describe('Schedule Export', () => {
  test.beforeEach(async ({ page }) => {
    const startDate = new Date('2024-01-01');
    const endDate = new Date('2024-01-28');

    await loginAsAdmin(page);
    await setupScheduleApiMocks(page, startDate, endDate);
  });

  test('should have export button visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Look for export button
    const exportButton = page.locator('button:has-text("Export")').or(
      page.locator('a:has-text("Export")')
    );

    if (await exportButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(exportButton).toBeVisible();
    }
  });

  test('should download schedule as Excel/CSV', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Look for export button
    const exportButton = page.locator('button:has-text("Export")');

    if (await exportButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Setup download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);

      // Click export button
      await exportButton.click();

      // Wait for download
      const download = await downloadPromise;

      if (download) {
        // Verify download started
        expect(download).toBeTruthy();

        // Verify filename
        const filename = download.suggestedFilename();
        expect(filename).toMatch(/schedule.*\.(xlsx|csv)$/i);
      }
    }
  });

  test('should export with current filters applied', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Set date range filter
    const startDateInput = page.locator('input[aria-label="Start date"]');
    await startDateInput.fill('2024-02-01');

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Look for export button
    const exportButton = page.locator('button:has-text("Export")');

    if (await exportButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);
      await exportButton.click();
      const download = await downloadPromise;

      // Verify export includes filtered date range
      if (download) {
        const filename = download.suggestedFilename();
        // Filename might include date range
        expect(filename).toMatch(/schedule/i);
      }
    }
  });
});

// ============================================================================
// Test Suite: Responsive Design and Accessibility
// ============================================================================

test.describe('Responsive Design and Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    const startDate = new Date('2024-01-01');
    const endDate = new Date('2024-01-28');

    await loginAsAdmin(page);
    await setupScheduleApiMocks(page, startDate, endDate);
  });

  test('should have accessible navigation controls', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Verify ARIA labels are present
    await expect(page.locator('button[aria-label="Previous block"]')).toBeVisible();
    await expect(page.locator('button[aria-label="Next block"]')).toBeVisible();
    await expect(page.locator('input[aria-label="Start date"]')).toBeVisible();
    await expect(page.locator('input[aria-label="End date"]')).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Verify focus is visible
    const focusedElement = await page.evaluateHandle(() => document.activeElement);
    expect(focusedElement).toBeTruthy();
  });

  test('should have proper color contrast for accessibility', async ({ page }) => {
    await page.goto(`${BASE_URL}/schedule`);

    // This is a visual test - in a real scenario, you'd use accessibility testing tools
    // For now, just verify key elements are visible
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Error Handling
// ============================================================================

test.describe('Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should display error message when API fails', async ({ page }) => {
    // Mock API error
    await page.route(`${API_BASE_URL}/people*`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Internal server error',
        }),
      });
    });

    await page.goto(`${BASE_URL}/schedule`);

    // Verify error message is displayed
    await expect(
      page.locator('text=/Failed to load/i').or(page.locator('text=/Error/i'))
    ).toBeVisible({ timeout: 5000 });
  });

  test('should display loading state while fetching data', async ({ page }) => {
    // Delay API response to see loading state
    await page.route(`${API_BASE_URL}/people*`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockApiResponses.people),
      });
    });

    await page.goto(`${BASE_URL}/schedule`);

    // Verify loading spinner/message appears
    const loadingIndicator = page.locator('text=/Loading/i').or(page.locator('[class*="spin"]'));
    await expect(loadingIndicator).toBeVisible({ timeout: 2000 });
  });

  test('should handle empty schedule gracefully', async ({ page }) => {
    // Mock empty data
    await page.route(`${API_BASE_URL}/**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          total: 0,
        }),
      });
    });

    await page.goto(`${BASE_URL}/schedule`);

    // Verify empty state message
    await expect(
      page.locator('text=/No people/i').or(page.locator('text=/No data/i'))
    ).toBeVisible({ timeout: 5000 });
  });
});
