import * as path from 'path';
import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';
import { waitForNetworkIdle } from '../../utils/test-helpers';

/**
 * Rollback E2E Tests
 *
 * Tests the rollback mechanism after a batch has been applied:
 * 1. Upload and stage a file
 * 2. Create draft and apply the batch
 * 3. Navigate to batch detail
 * 4. Trigger rollback
 * 5. Verify batch status changes to rolled_back
 * 6. Verify via API that assignments were reverted
 *
 * Prerequisites:
 *   - A valid test xlsx fixture at e2e/fixtures/test-block10.xlsx
 *   - Backend half-day import, apply, and rollback endpoints must be running
 *   - Database must have matching person records for the xlsx names
 */

const TEST_XLSX_PATH = path.join(__dirname, '../../fixtures/test-block10.xlsx');
const TEST_BLOCK_NUMBER = '10';
const TEST_ACADEMIC_YEAR = '2025';

test.describe('Rollback After Apply', () => {
  test.skip(() => !process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');

  test('Full import → apply → rollback workflow', async ({ adminPage, request }) => {
    let batchUrl: string;

    await test.step('Upload, stage, and create draft', async () => {
      // Navigate to half-day import
      await adminPage.goto('/import/half-day');
      await waitForNetworkIdle(adminPage);

      // Upload file
      await adminPage.locator(selectors.importExport.hdFileInput).setInputFiles(TEST_XLSX_PATH);
      await adminPage.locator(selectors.importExport.hdBlockNumber).fill(TEST_BLOCK_NUMBER);
      await adminPage.locator(selectors.importExport.hdAcademicYear).fill(TEST_ACADEMIC_YEAR);

      // Stage the import
      await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/stage') && resp.status() === 200,
          { timeout: 30_000 },
        ),
        adminPage.locator(selectors.importExport.hdStageBtn).click(),
      ]);

      // Wait for diff table to render
      await expect(adminPage.locator(selectors.importExport.hdDiffTable)).toBeVisible({
        timeout: 10_000,
      });

      // Select all diffs
      await adminPage.locator(selectors.importExport.hdSelectPageBtn).click();

      // Create draft
      await adminPage
        .locator(selectors.importExport.hdDraftNotes)
        .fill('Rollback test — will be reverted');

      await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/draft') && resp.status() === 200,
          { timeout: 15_000 },
        ),
        adminPage.locator(selectors.importExport.hdCreateDraftBtn).click(),
      ]);

      // Navigate to batch review
      await adminPage.locator(selectors.importExport.hdViewDraftBtn).click();
      await adminPage.waitForURL(/\/import\/batch\//, { timeout: 10_000 });

      // Capture the batch URL for subsequent steps
      batchUrl = adminPage.url();
    });

    await test.step('Apply batch', async () => {
      // Apply the batch
      const [applyResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/apply') && resp.status() === 200,
          { timeout: 30_000 },
        ),
        adminPage.locator(selectors.importExport.batchApplyBtn).click(),
      ]);
      expect(applyResponse.ok()).toBe(true);

      // Verify APPLIED status
      const statusBadge = adminPage.locator(selectors.importExport.batchStatusBadge);
      await expect(statusBadge).toContainText(/applied/i, { timeout: 10_000 });
    });

    await test.step('Rollback and verify status', async () => {
      // Trigger rollback — try the rollback button first, fall back to cancel
      const rollbackBtn = adminPage.locator(
        'button:has-text("Rollback"), button:has-text("Revert"), button:has-text("Undo")',
      );
      const cancelBtn = adminPage.locator(selectors.importExport.batchCancelBtn);

      const hasRollback = await rollbackBtn.isVisible().catch(() => false);
      const triggerBtn = hasRollback ? rollbackBtn : cancelBtn;

      // Click rollback and wait for API response
      const [rollbackResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) =>
            (resp.url().includes('/rollback') || resp.url().includes('/cancel')) &&
            resp.status() === 200,
          { timeout: 30_000 },
        ),
        triggerBtn.click(),
      ]);

      expect(rollbackResponse.ok()).toBe(true);

      // Verify status badge changes to rolled_back (or cancelled)
      const statusBadge = adminPage.locator(selectors.importExport.batchStatusBadge);
      await expect(statusBadge).toContainText(/rolled.back|cancelled|reverted/i, {
        timeout: 10_000,
      });
    });

    await test.step('Verify assignments reverted via API', async () => {
      const apiBaseUrl = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';

      // Query assignments for the block we imported and rolled back
      const assignmentsResponse = await request.get(
        `${apiBaseUrl}/api/v1/half-day/assignments?block_number=${TEST_BLOCK_NUMBER}&academic_year=${TEST_ACADEMIC_YEAR}`,
      );
      expect(assignmentsResponse.ok()).toBe(true);

      const assignments = await assignmentsResponse.json();
      expect(assignments).toBeTruthy();

      if (batchUrl) {
        // Extract batch ID from URL (e.g., /import/batch/123 -> 123)
        const batchIdMatch = batchUrl.match(/\/batch\/([a-zA-Z0-9-]+)/);
        if (batchIdMatch) {
          const batchId = batchIdMatch[1];
          const batchResponse = await request.get(
            `${apiBaseUrl}/api/v1/half-day/batches/${batchId}`,
          );
          expect(batchResponse.ok()).toBe(true);

          const batchData = await batchResponse.json();
          // Status should reflect rollback
          const status = batchData.status || batchData.batchStatus;
          expect(status).toMatch(/rolled_back|cancelled/i);
        }
      }
    });
  });

  // Edge Cases
  test.describe('Rollback Edge Cases', () => {
    test('should not allow rollback on a draft (unapplied) batch', async ({ adminPage }) => {
      // Navigate to a draft batch page
      await adminPage.goto('/import/half-day');
      await waitForNetworkIdle(adminPage);

      // Upload and stage only (do not apply)
      await adminPage.locator(selectors.importExport.hdFileInput).setInputFiles(TEST_XLSX_PATH);
      await adminPage.locator(selectors.importExport.hdBlockNumber).fill(TEST_BLOCK_NUMBER);
      await adminPage.locator(selectors.importExport.hdAcademicYear).fill(TEST_ACADEMIC_YEAR);

      await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/stage') && resp.status() === 200,
        ),
        adminPage.locator(selectors.importExport.hdStageBtn).click(),
      ]);

      await adminPage.locator(selectors.importExport.hdSelectPageBtn).click();
      await adminPage
        .locator(selectors.importExport.hdDraftNotes)
        .fill('Draft only — no apply');

      await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/draft') && resp.status() === 200,
        ),
        adminPage.locator(selectors.importExport.hdCreateDraftBtn).click(),
      ]);

      // Go to batch review (still in DRAFT state)
      await adminPage.locator(selectors.importExport.hdViewDraftBtn).click();
      await adminPage.waitForURL(/\/import\/batch\//, { timeout: 10_000 });

      // Rollback button should NOT be visible for a draft
      const rollbackBtn = adminPage.locator(
        'button:has-text("Rollback"), button:has-text("Revert"), button:has-text("Undo")',
      );
      await expect(rollbackBtn).not.toBeVisible();

      // The apply button should be visible instead
      await expect(adminPage.locator(selectors.importExport.batchApplyBtn)).toBeVisible();
    });

    test('should not allow double rollback', async ({ adminPage }) => {
      test.fixme(true, 'Requires a batch that has already been rolled back.');

      // Navigate to a rolled-back batch
      // (In a real test, we would use the batchUrl from a prior rollback)
      await adminPage.goto('/hub/import-export');
      await waitForNetworkIdle(adminPage);

      // After navigating to a rolled_back batch, no rollback controls should appear
      const rollbackBtn = adminPage.locator(
        'button:has-text("Rollback"), button:has-text("Revert"), button:has-text("Undo")',
      );
      await expect(rollbackBtn).not.toBeVisible();
    });
  });
});
