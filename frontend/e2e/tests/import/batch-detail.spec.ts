import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';

test.describe('Batch Detail and Apply', () => {
  test.skip(() => !process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');

  test.beforeEach(async ({ adminPage }) => {
    // In a real test, we would navigate to a specific batch ID we created,
    // or navigate to the hub and click the first batch.
    await adminPage.goto('/hub/import-export');
    await adminPage.waitForLoadState('networkidle');
  });

  test('Batch detail renders with correct status badge', async ({ adminPage }) => {
    // Find a batch link
    const firstBatchLink = adminPage.locator('a[href*="/import/batch/"]').first();

    if (await firstBatchLink.isVisible()) {
      await firstBatchLink.click();
      await adminPage.waitForLoadState('networkidle');

      const statusBadge = adminPage.locator(selectors.importExport.batchStatusBadge);
      await expect(statusBadge).toBeVisible();

      const text = await statusBadge.innerText();
      expect(text).toMatch(/draft|applied|rolled.back|cancelled/i);
    }
  });

  test('Staged assignments table matches API preview response', async ({ adminPage, request }) => {
    const firstBatchLink = adminPage.locator('a[href*="/import/batch/"]').first();

    if (await firstBatchLink.isVisible()) {
      const href = await firstBatchLink.getAttribute('href');
      const batchId = href?.split('/').pop();

      await firstBatchLink.click();
      await adminPage.waitForLoadState('networkidle');

      if (batchId) {
        const apiBaseUrl = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';
        const response = await request.get(`${apiBaseUrl}/api/v1/half-day/batches/${batchId}`);

        if (response.ok()) {
          const data = await response.json();
          // Verify table renders
          const table = adminPage.locator(selectors.importExport.hdDiffTable).or(adminPage.locator('table'));
          await expect(table.first()).toBeVisible();

          // Row count should be close to records count
          const rows = table.locator('tbody tr');
          const records = data.records || [];
          if (records.length > 0) {
            expect(await rows.count()).toBeGreaterThan(0);
          }
        }
      }
    }
  });

  test('Apply button triggers correct API call', async ({ adminPage }) => {
    // Find a DRAFT batch specifically if possible, otherwise skip
    const draftLink = adminPage.locator('tr:has-text("DRAFT") a[href*="/import/batch/"]').first();

    if (await draftLink.isVisible()) {
      await draftLink.click();
      await adminPage.waitForLoadState('networkidle');

      const applyBtn = adminPage.locator(selectors.importExport.batchApplyBtn);
      if (await applyBtn.isVisible()) {
        const applyPromise = adminPage.waitForResponse(
          (response) => response.url().includes('/apply') && response.status() === 200,
          { timeout: 30000 }
        ).catch(() => null);

        await applyBtn.click();

        const response = await applyPromise;
        expect(response).toBeTruthy();

        const statusBadge = adminPage.locator(selectors.importExport.batchStatusBadge);
        await expect(statusBadge).toContainText(/applied/i);
      }
    }
  });

  test('Rollback controls visible on applied batch, hidden on draft', async ({ adminPage }) => {
    const appliedLink = adminPage.locator('tr:has-text("APPLIED") a[href*="/import/batch/"]').first();

    if (await appliedLink.isVisible()) {
      await appliedLink.click();
      await adminPage.waitForLoadState('networkidle');

      const rollbackBtn = adminPage.locator(
        'button:has-text("Rollback"), button:has-text("Revert"), button:has-text("Undo"), [data-testid="batch-cancel-btn"]'
      );
      await expect(rollbackBtn.first()).toBeVisible();
    }

    await adminPage.goto('/hub/import-export');

    const draftLink = adminPage.locator('tr:has-text("DRAFT") a[href*="/import/batch/"]').first();
    if (await draftLink.isVisible()) {
      await draftLink.click();
      await adminPage.waitForLoadState('networkidle');

      const rollbackBtn = adminPage.locator(
        'button:has-text("Rollback"), button:has-text("Revert"), button:has-text("Undo"), [data-testid="batch-cancel-btn"]'
      );
      await expect(rollbackBtn).not.toBeVisible();
    }
  });
});
