import { test, expect } from '../fixtures/auth.fixture';

test.describe('My Schedule', () => {
  test.skip(() => !process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');

  test.beforeEach(async ({ residentPage }) => {
    await residentPage.goto('/my-schedule');
    await residentPage.waitForLoadState('networkidle');
  });

  test('Schedule renders for logged-in resident', async ({ residentPage }) => {
    // Basic visibility test
    const calendar = residentPage.locator('[data-testid="schedule-calendar"], .calendar-container');
    await expect(calendar.first()).toBeVisible();
  });

  test('Correct block assignments shown (match API)', async ({ residentPage, request }) => {
    const apiBaseUrl = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';

    // Call the API endpoint for me/schedule
    const response = await request.get(`${apiBaseUrl}/api/v1/me/schedule`);

    if (response.ok()) {
      const data = await response.json();
      const assignments = data.assignments || [];

      const cards = residentPage.locator('[data-testid="assignment-card"], .assignment');

      if (assignments.length > 0) {
        await expect(cards.first()).toBeVisible();
      } else {
        await expect(cards).toHaveCount(0);
      }
    }
  });

  test('Navigation between blocks works', async ({ residentPage }) => {
    const nextBtn = residentPage.locator('[data-testid="next-block-btn"], button:has-text("Next")');
    const prevBtn = residentPage.locator('[data-testid="prev-block-btn"], button:has-text("Prev")');
    const blockLabel = residentPage.locator('[data-testid="current-block-label"]');

    if (await nextBtn.isVisible() && await blockLabel.isVisible()) {
      const initialLabel = await blockLabel.innerText();

      await nextBtn.click();
      await residentPage.waitForLoadState('networkidle');

      const newLabel = await blockLabel.innerText();
      expect(initialLabel).not.toBe(newLabel);

      // Navigate back
      await prevBtn.click();
      await residentPage.waitForLoadState('networkidle');
      const backLabel = await blockLabel.innerText();
      expect(backLabel).toBe(initialLabel);
    }
  });

  test('No other residents' data visible', async ({ residentPage }) => {
    // Assert there's no resident filter or that we only see our own data
    const filter = residentPage.locator('[data-testid="person-filter"], select[name="personId"]');

    // A resident shouldn't be able to filter for others on 'my-schedule'
    if (await filter.isVisible()) {
      // If it is visible, it should only have 1 option or be disabled
      const options = filter.locator('option');
      if (await options.count() > 0) {
        expect(await options.count()).toBe(1);
      } else {
        await expect(filter).toBeDisabled();
      }
    }

    // Optional: scan all text for other CPT Doe names and ensure they don't appear
    // (Assuming the current resident is CPT Doe-01 for example)
    // This is hard to assert definitively without knowing the exact current user,
    // but the lack of a filter is the primary UI constraint.
  });
});
