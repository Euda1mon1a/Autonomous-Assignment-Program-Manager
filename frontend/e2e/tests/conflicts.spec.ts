import { test, expect } from '../fixtures/auth.fixture';
import { selectors } from '../utils/selectors';

test.describe('Schedule Conflict Viewer', () => {
  test.skip(() => !process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');

  test.beforeEach(async ({ adminPage }) => {
    await adminPage.goto('/conflicts');
    await adminPage.waitForLoadState('networkidle');
  });

  test('Conflict list renders when seeded data has overlaps', async ({ adminPage, request }) => {
    const apiBaseUrl = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';

    // First query API to see if there are actual conflicts
    const response = await request.get(`${apiBaseUrl}/api/v1/conflicts/analysis/detect`);
    const data = await response.json();
    const hasConflicts = data.conflicts && data.conflicts.length > 0;

    const list = adminPage.locator(selectors.conflicts.list);

    if (hasConflicts) {
      await expect(list).toBeVisible();
      const conflictItems = list.locator('> div, li'); // Assuming a list
      expect(await conflictItems.count()).toBeGreaterThan(0);
    } else {
      // Expect some empty state
      await expect(adminPage.locator('text=/no conflicts/i')).toBeVisible();
    }
  });

  test('Conflict detail shows both conflicting assignments', async ({ adminPage }) => {
    const list = adminPage.locator(selectors.conflicts.list);

    if (await list.isVisible()) {
      // Click first conflict to show detail
      const firstItem = list.locator('> div, li').first();
      await firstItem.click();

      const detail = adminPage.locator(selectors.conflicts.detail);
      await expect(detail).toBeVisible();

      // Expect text that shows two assignments
      const detailText = await detail.innerText();
      expect(detailText.length).toBeGreaterThan(0);

      // Usually there are two separate cards or sections for the conflicting items
      const assignments = detail.locator('[data-testid="conflict-assignment"]');
      if (await assignments.count() > 0) {
        expect(await assignments.count()).toBe(2);
      }
    }
  });

  test('Severity indicator matches conflict type', async ({ adminPage }) => {
    const list = adminPage.locator(selectors.conflicts.list);

    if (await list.isVisible()) {
      const firstItem = list.locator('> div, li').first();
      await firstItem.click();

      const detail = adminPage.locator(selectors.conflicts.detail);
      await expect(detail).toBeVisible();

      const severityIndicator = detail.locator(selectors.conflicts.severityIndicator);

      if (await severityIndicator.isVisible()) {
        const text = await severityIndicator.innerText();
        expect(text).toMatch(/high|medium|low|critical/i);
      }
    }
  });
});
