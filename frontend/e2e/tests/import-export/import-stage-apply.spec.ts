import * as path from 'path';
import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';
import { waitForNetworkIdle } from '../../utils/test-helpers';

/**
 * Import Stage & Apply E2E Tests
 *
 * Tests the full half-day import pipeline:
 * 1. Upload xlsx file
 * 2. Fill block metadata (block number, academic year)
 * 3. Stage the import (diff computation)
 * 4. Review diff metrics
 * 5. Create draft / apply batch
 *
 * Prerequisites:
 *   - A valid test xlsx fixture at e2e/fixtures/test-block10.xlsx
 *   - Backend half-day import endpoints must be running
 *   - Database must have matching person records for the xlsx names
 */

// TODO: Create this fixture file with representative block data
const TEST_XLSX_PATH = path.join(__dirname, '../../fixtures/test-block10.xlsx');
const TEST_BLOCK_NUMBER = '10';
const TEST_ACADEMIC_YEAR = '2025';

test.describe('Import Stage & Apply', () => {
  test.beforeEach(async ({ adminPage }) => {
    // Navigate to the half-day import page
    await adminPage.goto('/import/half-day');
    await waitForNetworkIdle(adminPage);
  });

  // --------------------------------------------------------------------------
  // Upload Step
  // --------------------------------------------------------------------------

  test.describe('File Upload', () => {
    test('should display upload form with required fields', async ({ adminPage }) => {
      const fileInput = adminPage.locator(selectors.importExport.hdFileInput);
      const blockNumber = adminPage.locator(selectors.importExport.hdBlockNumber);
      const academicYear = adminPage.locator(selectors.importExport.hdAcademicYear);
      const stageBtn = adminPage.locator(selectors.importExport.hdStageBtn);

      await expect(fileInput).toBeAttached();
      await expect(blockNumber).toBeVisible();
      await expect(academicYear).toBeVisible();
      await expect(stageBtn).toBeVisible();
    });

    test('should accept an xlsx file and populate metadata fields', async ({ adminPage }) => {
      // TODO: Requires test-block10.xlsx fixture file. Remove test.fixme() once created.
      test.fixme();

      // Upload the test fixture
      await adminPage.locator(selectors.importExport.hdFileInput).setInputFiles(TEST_XLSX_PATH);

      // Fill block metadata
      await adminPage.locator(selectors.importExport.hdBlockNumber).fill(TEST_BLOCK_NUMBER);
      await adminPage.locator(selectors.importExport.hdAcademicYear).fill(TEST_ACADEMIC_YEAR);

      // Stage button should be enabled now
      const stageBtn = adminPage.locator(selectors.importExport.hdStageBtn);
      await expect(stageBtn).toBeEnabled();
    });

    test('should prevent staging without required fields', async ({ adminPage }) => {
      // Try to click stage without uploading a file
      const stageBtn = adminPage.locator(selectors.importExport.hdStageBtn);

      // Button should be disabled or clicking should show validation
      const isDisabled = await stageBtn.isDisabled().catch(() => false);
      if (!isDisabled) {
        await stageBtn.click();
        // Expect some validation feedback (toast, inline error, etc.)
        await adminPage.waitForTimeout(500);
      }

      // We should still be on the upload step (no navigation to preview)
      await expect(adminPage).toHaveURL(/\/import\/half-day/);
    });
  });

  // --------------------------------------------------------------------------
  // Staging Step
  // --------------------------------------------------------------------------

  test.describe('Staging & Diff Preview', () => {
    test('should stage import and display diff metrics', async ({ adminPage }) => {
      // TODO: Requires test-block10.xlsx fixture AND matching person records in DB.
      // Remove test.fixme() once both prerequisites are met.
      test.fixme();

      // Upload file and fill metadata
      await adminPage.locator(selectors.importExport.hdFileInput).setInputFiles(TEST_XLSX_PATH);
      await adminPage.locator(selectors.importExport.hdBlockNumber).fill(TEST_BLOCK_NUMBER);
      await adminPage.locator(selectors.importExport.hdAcademicYear).fill(TEST_ACADEMIC_YEAR);

      // Click stage and wait for the staging API response
      const [stageResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/stage') && resp.status() === 200,
          { timeout: 30_000 },
        ),
        adminPage.locator(selectors.importExport.hdStageBtn).click(),
      ]);

      expect(stageResponse.ok()).toBe(true);

      // Verify diff metric badges are visible
      const metricTotal = adminPage.locator(selectors.importExport.hdMetricTotal);
      const metricChanged = adminPage.locator(selectors.importExport.hdMetricChanged);
      const metricAddedRemoved = adminPage.locator(selectors.importExport.hdMetricAddedRemoved);
      const metricHours = adminPage.locator(selectors.importExport.hdMetricHours);

      await expect(metricTotal).toBeVisible({ timeout: 10_000 });
      await expect(metricChanged).toBeVisible();
      await expect(metricAddedRemoved).toBeVisible();
      await expect(metricHours).toBeVisible();
    });

    test('should display diff table with filterable rows', async ({ adminPage }) => {
      // TODO: Requires staged data from prior step. Remove test.fixme() once fixture exists.
      test.fixme();

      // Upload, fill, and stage
      await adminPage.locator(selectors.importExport.hdFileInput).setInputFiles(TEST_XLSX_PATH);
      await adminPage.locator(selectors.importExport.hdBlockNumber).fill(TEST_BLOCK_NUMBER);
      await adminPage.locator(selectors.importExport.hdAcademicYear).fill(TEST_ACADEMIC_YEAR);

      await Promise.all([
        adminPage.waitForResponse((resp) => resp.url().includes('/stage') && resp.status() === 200),
        adminPage.locator(selectors.importExport.hdStageBtn).click(),
      ]);

      // Diff table should appear
      const diffTable = adminPage.locator(selectors.importExport.hdDiffTable);
      await expect(diffTable).toBeVisible({ timeout: 10_000 });

      // Filter controls should be present
      await expect(adminPage.locator(selectors.importExport.hdFilterDiffType)).toBeVisible();
      await expect(adminPage.locator(selectors.importExport.hdFilterActivity)).toBeVisible();
      await expect(adminPage.locator(selectors.importExport.hdFilterPerson)).toBeVisible();

      // Pagination should be present
      await expect(adminPage.locator(selectors.importExport.hdPaginationInfo)).toBeVisible();
    });

    test('should allow selecting diffs and creating a draft', async ({ adminPage }) => {
      // TODO: Requires staged data. Remove test.fixme() once fixture exists.
      test.fixme();

      // Upload, fill, and stage
      await adminPage.locator(selectors.importExport.hdFileInput).setInputFiles(TEST_XLSX_PATH);
      await adminPage.locator(selectors.importExport.hdBlockNumber).fill(TEST_BLOCK_NUMBER);
      await adminPage.locator(selectors.importExport.hdAcademicYear).fill(TEST_ACADEMIC_YEAR);

      await Promise.all([
        adminPage.waitForResponse((resp) => resp.url().includes('/stage') && resp.status() === 200),
        adminPage.locator(selectors.importExport.hdStageBtn).click(),
      ]);

      // Wait for diff table
      await expect(adminPage.locator(selectors.importExport.hdDiffTable)).toBeVisible({
        timeout: 10_000,
      });

      // Select all diffs on the current page
      await adminPage.locator(selectors.importExport.hdSelectPageBtn).click();

      // Fill draft notes
      await adminPage.locator(selectors.importExport.hdDraftNotes).fill('E2E test draft');

      // Create draft and wait for response
      const [draftResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/draft') && resp.status() === 200,
          { timeout: 15_000 },
        ),
        adminPage.locator(selectors.importExport.hdCreateDraftBtn).click(),
      ]);

      expect(draftResponse.ok()).toBe(true);

      // Draft summary metrics should be visible
      await expect(adminPage.locator(selectors.importExport.hdDraftAdded)).toBeVisible();
      await expect(adminPage.locator(selectors.importExport.hdDraftModified)).toBeVisible();
      await expect(adminPage.locator(selectors.importExport.hdDraftRemoved)).toBeVisible();
    });
  });

  // --------------------------------------------------------------------------
  // Batch Review & Apply
  // --------------------------------------------------------------------------

  test.describe('Batch Apply', () => {
    test('should navigate to batch review and apply', async ({ adminPage }) => {
      // TODO: Requires a DRAFT batch to exist (from staging workflow above).
      // Remove test.fixme() once end-to-end seeding is available.
      test.fixme();

      // Assume we landed on the draft step — navigate to batch review
      await adminPage.locator(selectors.importExport.hdViewDraftBtn).click();
      await adminPage.waitForURL(/\/import\/batch\//, { timeout: 10_000 });

      // Verify batch review elements
      const statusBadge = adminPage.locator(selectors.importExport.batchStatusBadge);
      await expect(statusBadge).toBeVisible();
      await expect(statusBadge).toContainText(/draft/i);

      // Verify preview stats
      await expect(adminPage.locator(selectors.importExport.batchStatNew)).toBeVisible();
      await expect(adminPage.locator(selectors.importExport.batchStatUpdates)).toBeVisible();

      // Apply the batch
      const [applyResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/apply') && resp.status() === 200,
          { timeout: 30_000 },
        ),
        adminPage.locator(selectors.importExport.batchApplyBtn).click(),
      ]);

      expect(applyResponse.ok()).toBe(true);

      // Status badge should update to APPLIED
      await expect(statusBadge).toContainText(/applied/i, { timeout: 10_000 });
    });
  });
});
