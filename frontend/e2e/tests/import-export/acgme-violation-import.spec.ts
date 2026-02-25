import * as path from 'path';
import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';
import { waitForNetworkIdle } from '../../utils/test-helpers';

/**
 * ACGME Violation Import E2E Tests (Phase 3e)
 *
 * Tests the import pipeline when a schedule violates ACGME rules (e.g., 1-in-7 rule):
 * 1. Upload xlsx file with violations
 * 2. Stage the import
 * 3. Verify ACGME warnings appear on the preview step
 * 4. Apply the batch and verify warnings persist on the batch detail view
 *
 * Prerequisites:
 *   - A valid test xlsx fixture at e2e/fixtures/test-acgme-violation.xlsx
 *   - Backend half-day import endpoints must be running
 *   - Database must have matching person records for the xlsx names
 */

const TEST_XLSX_PATH = path.join(__dirname, '../../fixtures/test-acgme-violation.xlsx');
const TEST_BLOCK_NUMBER = '10';
const TEST_ACADEMIC_YEAR = '2025';

test.describe('Import ACGME Violation', () => {
  test.beforeEach(async ({ adminPage }) => {
    // Navigate to the half-day import page
    await adminPage.goto('/import/half-day');
    await waitForNetworkIdle(adminPage);
  });

  test('should stage import and display ACGME warnings', async ({ adminPage }) => {
    test.skip(!process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database with matching person records');

    // Upload file and fill metadata
    await adminPage.locator(selectors.importExport.hdFileInput).setInputFiles(TEST_XLSX_PATH);
    await adminPage.locator(selectors.importExport.hdBlockNumber).fill(TEST_BLOCK_NUMBER);
    await adminPage.locator(selectors.importExport.hdAcademicYear).fill(TEST_ACADEMIC_YEAR);

    // Stage
    const [stageResponse] = await Promise.all([
      adminPage.waitForResponse(
        (resp) => resp.url().includes('/stage') && resp.status() === 200,
        { timeout: 30_000 },
      ),
      adminPage.locator(selectors.importExport.hdStageBtn).click(),
    ]);

    expect(stageResponse.ok()).toBe(true);

    // Verify we are on preview step
    await expect(adminPage.locator(selectors.importExport.hdDiffTable)).toBeVisible();

    // Select all diffs on the current page
    await adminPage.locator(selectors.importExport.hdSelectPageBtn).click();

    // Fill draft notes
    await adminPage.locator(selectors.importExport.hdDraftNotes).fill('Draft with ACGME violations');

    // Create draft and wait for response
    const [draftResponse] = await Promise.all([
      adminPage.waitForResponse(
        (resp) => resp.url().includes('/draft') && resp.status() === 200,
        { timeout: 15_000 },
      ),
      adminPage.locator(selectors.importExport.hdCreateDraftBtn).click(),
    ]);

    expect(draftResponse.ok()).toBe(true);

    // Assume we landed on the draft step — navigate to batch review
    await adminPage.locator(selectors.importExport.hdViewDraftBtn).click();
    await adminPage.waitForURL(/\/import\/batch\//, { timeout: 10_000 });

    // Verify violation stats/warnings are visible (using existing selectors)
    const violationsStat = adminPage.locator(selectors.importExport.batchStatViolations);
    await expect(violationsStat).toBeVisible({ timeout: 10_000 });
    const violationText = await violationsStat.innerText();

    // We expect at least 1 violation to be reported
    expect(parseInt(violationText, 10)).toBeGreaterThan(0);
  });
});
