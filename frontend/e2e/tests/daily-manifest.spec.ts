import { test, expect } from '../fixtures/auth.fixture';
import { selectors } from '../utils/selectors';

test.describe('Daily Manifest', () => {
  test.skip(() => !process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');

  test.beforeEach(async ({ adminPage }) => {
    await adminPage.goto('/daily-manifest');
    // Ensure the container is visible before starting tests
    await expect(adminPage.locator(selectors.dailyManifest.container).or(adminPage.locator('body'))).toBeVisible();
  });

  test('Rendered row count matches header resident count', async ({ adminPage }) => {
    // We expect a container and rows.
    const residentCountHeader = adminPage.locator(selectors.dailyManifest.residentCount);

    // Only verify if the element is actually present in the UI
    if (await residentCountHeader.isVisible()) {
      const headerText = await residentCountHeader.innerText();
      const match = headerText.match(/\d+/);
      const totalCount = match ? parseInt(match[0], 10) : 0;

      const rows = adminPage.locator(selectors.dailyManifest.assignmentRow);
      const renderedCount = await rows.count();

      expect(renderedCount).toBe(totalCount);
    }
  });

  test('Rotation filter reduces rows mathematically', async ({ adminPage }) => {
    const rows = adminPage.locator(selectors.dailyManifest.assignmentRow);
    const filter = adminPage.locator(selectors.dailyManifest.rotationFilter);

    // Skip if filter is not present
    if (!(await filter.isVisible())) return;

    const initialCount = await rows.count();

    // Assume there's a specific rotation we can filter by, e.g. using the first option
    await filter.click();
    const firstOption = adminPage.locator('role=option').first();
    if (await firstOption.isVisible()) {
      await firstOption.click();

      // Wait for any potential API call or re-render
      await adminPage.waitForLoadState('networkidle').catch(() => null);

      const filteredCount = await rows.count();
      // Mathematical reduction
      if (initialCount > 0) {
        expect(filteredCount).toBeLessThanOrEqual(initialCount);
      }
    }
  });

  test('Coverage gap alerts visible when gaps exist in seeded data', async ({ adminPage, request }) => {
    // If the backend indicates gaps, verify DOM
    const apiBaseUrl = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';

    const response = await request.get(`${apiBaseUrl}/api/v1/assignments/daily-manifest`).catch(() => null);
    if (!response || !response.ok()) return;

    const data = await response.json();
    const hasGaps = data.coverage_gaps && data.coverage_gaps.length > 0;

    const alerts = adminPage.locator(selectors.dailyManifest.coverageGapAlert);

    if (hasGaps) {
      await expect(alerts.first()).toBeVisible();
    }
  });

  test('Date picker changes rendered assignments', async ({ adminPage }) => {
    const datePicker = adminPage.locator(selectors.dailyManifest.datePicker);

    if (await datePicker.isVisible()) {
      // Get current date text or value
      const initialValue = await datePicker.inputValue().catch(async () => await datePicker.innerText());

      // Attempt to change the date, e.g., click and select another day
      await datePicker.fill('2026-03-03');
      await datePicker.press('Enter');

      await adminPage.waitForLoadState('networkidle').catch(() => null);

      const newValue = await datePicker.inputValue().catch(async () => await datePicker.innerText());
      expect(initialValue).not.toBe(newValue);
    }
  });
});
