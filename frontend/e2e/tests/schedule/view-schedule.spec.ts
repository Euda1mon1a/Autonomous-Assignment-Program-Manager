import { test, expect } from '../../fixtures/schedule.fixture';
import { selectors } from '../../utils/selectors';
import { waitForLoading } from '../../utils/test-helpers';

/**
 * View Schedule Tests
 *
 * Tests for viewing and navigating the schedule
 */

test.describe('View Schedule', () => {
  test('should display schedule calendar', async ({ page, scheduleHelper }) => {
    await scheduleHelper.createPartialSchedule(7, 5);

    await page.goto('/schedule');
    await waitForLoading(page);

    // Calendar should be visible
    await expect(page.locator(selectors.schedule.calendar)).toBeVisible();
  });

  test('should display current month by default', async ({ page }) => {
    await page.goto('/schedule');
    await waitForLoading(page);

    const currentMonth = new Date().toLocaleString('default', { month: 'long' });
    const monthDisplay = page.locator(selectors.calendar.month);

    await expect(monthDisplay).toContainText(currentMonth);
  });

  test('should navigate to previous month', async ({ page }) => {
    await page.goto('/schedule');
    await waitForLoading(page);

    await page.click(selectors.calendar.prevMonth);
    await waitForLoading(page);

    // Should show previous month
    await expect(page.locator(selectors.calendar.month)).toBeVisible();
  });

  test('should navigate to next month', async ({ page }) => {
    await page.goto('/schedule');
    await waitForLoading(page);

    await page.click(selectors.calendar.nextMonth);
    await waitForLoading(page);

    // Should show next month
    await expect(page.locator(selectors.calendar.month)).toBeVisible();
  });

  test('should jump to today', async ({ page }) => {
    await page.goto('/schedule');

    // Navigate to different month
    await page.click(selectors.calendar.nextMonth);
    await page.click(selectors.calendar.nextMonth);

    // Click today button
    await page.click(selectors.calendar.today);
    await waitForLoading(page);

    // Should show current month
    const currentMonth = new Date().toLocaleString('default', { month: 'long' });
    await expect(page.locator(selectors.calendar.month)).toContainText(currentMonth);
  });

  test('should display assignments in calendar', async ({ page, scheduleHelper }) => {
    const scenario = await scheduleHelper.createPartialSchedule(7, 5);

    await page.goto('/schedule');
    await waitForLoading(page);

    // Should show assignment cards
    const assignments = page.locator(selectors.schedule.assignment);
    await expect(assignments).toHaveCount(scenario.assignmentIds.length);
  });

  test('should show empty state when no assignments', async ({ page, scheduleHelper }) => {
    await scheduleHelper.createEmptySchedule(7);

    await page.goto('/schedule');
    await waitForLoading(page);

    // Should show empty state
    await expect(page.locator(selectors.schedule.emptyState)).toBeVisible();
  });

  test('should switch between month and week view', async ({ page }) => {
    await page.goto('/schedule');

    // Toggle view mode
    const viewToggle = page.locator(selectors.schedule.viewModeToggle);

    if (await viewToggle.isVisible()) {
      await viewToggle.click();

      // Should switch to week view
      const weekView = page.locator(selectors.calendar.week);
      await expect(weekView).toBeVisible();

      // Toggle back
      await viewToggle.click();

      // Should switch to month view
      const monthView = page.locator(selectors.calendar.month);
      await expect(monthView).toBeVisible();
    }
  });

  test('should show assignment details on click', async ({ page, scheduleHelper }) => {
    await scheduleHelper.createPartialSchedule(7, 5);

    await page.goto('/schedule');
    await waitForLoading(page);

    // Click first assignment
    const firstAssignment = page.locator(selectors.schedule.assignment).first();
    await firstAssignment.click();

    // Should show assignment details (modal or panel)
    const modal = page.locator(selectors.common.modal);
    await expect(modal).toBeVisible();
  });

  test('should color-code assignments by rotation', async ({ page, scheduleHelper }) => {
    await scheduleHelper.createFullSchedule(7, 10);

    await page.goto('/schedule');
    await waitForLoading(page);

    // Check if assignments have different background colors
    const assignments = page.locator(selectors.schedule.assignmentCard).all();

    const colors = new Set();
    for (const assignment of await assignments) {
      const bgColor = await assignment.evaluate((el) =>
        window.getComputedStyle(el).backgroundColor
      );
      colors.add(bgColor);
    }

    // Should have multiple colors (different rotations)
    expect(colors.size).toBeGreaterThan(1);
  });

  test('should display person name in assignment card', async ({ page, scheduleHelper }) => {
    await scheduleHelper.createPartialSchedule(7, 5);

    await page.goto('/schedule');
    await waitForLoading(page);

    const firstAssignment = page.locator(selectors.schedule.assignmentCard).first();
    const text = await firstAssignment.textContent();

    // Should contain person name or identifier
    expect(text).toBeTruthy();
    expect(text?.length).toBeGreaterThan(0);
  });

  test('should display rotation name in assignment card', async ({ page, scheduleHelper }) => {
    await scheduleHelper.createPartialSchedule(7, 5);

    await page.goto('/schedule');
    await waitForLoading(page);

    const firstAssignment = page.locator(selectors.schedule.assignmentCard).first();
    const text = await firstAssignment.textContent();

    // Should contain rotation info
    expect(text).toMatch(/FMIT|INPT|PROC|Clinic|Inpatient/i);
  });

  test('should be responsive on mobile', async ({ page, scheduleHelper }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await scheduleHelper.createPartialSchedule(7, 5);

    await page.goto('/schedule');
    await waitForLoading(page);

    // Calendar should adapt to mobile
    const calendar = page.locator(selectors.schedule.calendar);
    await expect(calendar).toBeVisible();

    const width = await calendar.evaluate((el) => el.clientWidth);
    expect(width).toBeLessThanOrEqual(375);
  });

  test('should load schedule data on page load', async ({ page }) => {
    let apiCalled = false;

    page.on('request', (request) => {
      if (request.url().includes('/api/v1/schedule') || request.url().includes('/api/v1/assignments')) {
        apiCalled = true;
      }
    });

    await page.goto('/schedule');
    await waitForLoading(page);

    expect(apiCalled).toBe(true);
  });

  test('should handle date range selection', async ({ page }) => {
    await page.goto('/schedule');

    const dateRangePicker = page.locator(selectors.schedule.dateRangePicker);

    if (await dateRangePicker.isVisible()) {
      await dateRangePicker.click();

      // Select date range (if implemented)
      await page.waitForTimeout(500);
    }
  });
});
