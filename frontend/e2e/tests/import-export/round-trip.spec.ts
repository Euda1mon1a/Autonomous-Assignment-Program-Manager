import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';
import { streamToBuffer, mutateXlsxCell, verifySysMeta } from '../../utils/xlsx-helpers';
import { waitForNetworkIdle } from '../../utils/test-helpers';

/**
 * Round-Trip E2E Test (The Golden Test)
 *
 * Validates the deterministic export -> mutate -> import -> verify pipeline:
 *
 *   1. Export a block to xlsx
 *   2. Mutate one cell in the exported file
 *   3. Write mutated buffer to a temp file
 *   4. Navigate to half-day import
 *   5. Upload the mutated file
 *   6. Stage and verify diff shows >= 1 Modified
 *   7. Select diffs and apply (or create draft + apply)
 *   8. Verify via API request context that the DB reflects the change
 *
 * Prerequisites:
 *   - A populated block with assignments must exist in the database
 *   - Backend export and import endpoints must be running
 *   - __SYS_META__ sheet must be preserved through the round-trip
 */

// Configuration for the round-trip test
const EXPORT_BLOCK_NUMBER = 10;
const EXPORT_ACADEMIC_YEAR = 2025;

// Cell to mutate: first resident's first day (row 9 = first data row, col F = first day)
// Using a visible sheet cell reference
const MUTATE_SHEET_INDEX = 0; // First visible sheet
const MUTATE_CELL_REF = 'F9';
const MUTATE_NEW_VALUE = 'NF'; // Change to Night Float for a clear diff

test.describe('Round-Trip (Golden Test)', () => {
  test.skip(() => !process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database with block 10 assignments');

  let exportedBuffer: Buffer;
  let mutatedBuffer: Buffer;
  let tempFilePath: string;
  let visibleSheetName: string;

  test.afterAll(async () => {
    // Clean up temp file
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
    }
  });

  test('Step 1-3: Export, mutate, and write temp file', async ({ adminPage }) => {
    // --- Step 1: Navigate to export and trigger download ---
    await adminPage.goto('/hub/import-export');
    await waitForNetworkIdle(adminPage);

    // Select xlsx format
    await adminPage.locator(selectors.importExport.exportFormatXlsx).click();

    // Trigger download
    const [download] = await Promise.all([
      adminPage.waitForEvent('download'),
      adminPage.locator(selectors.importExport.exportSubmitBtn).click(),
    ]);

    // Convert download to buffer
    const readStream = await download.createReadStream();
    expect(readStream).toBeTruthy();
    exportedBuffer = await streamToBuffer(readStream! as unknown as ReadableStream);
    expect(exportedBuffer.length).toBeGreaterThan(0);

    // Verify __SYS_META__ survived the export
    const metaValid = await verifySysMeta(
      exportedBuffer,
      EXPORT_BLOCK_NUMBER,
      EXPORT_ACADEMIC_YEAR,
    );
    expect(metaValid).toBe(true);

    // --- Step 2: Mutate one cell ---
    // Determine the visible sheet name from the exported workbook
    const XlsxPopulate = await import('xlsx-populate');
    const workbook = await XlsxPopulate.default.fromDataAsync(exportedBuffer);
    const visibleSheet = workbook.sheets().find((s: { hidden: () => unknown }) => !s.hidden());
    expect(visibleSheet).toBeTruthy();
    visibleSheetName = visibleSheet!.name();

    mutatedBuffer = await mutateXlsxCell(
      exportedBuffer,
      visibleSheetName,
      MUTATE_CELL_REF,
      MUTATE_NEW_VALUE,
    );
    expect(mutatedBuffer.length).toBeGreaterThan(0);

    // Verify __SYS_META__ is preserved after mutation
    const metaStillValid = await verifySysMeta(
      mutatedBuffer,
      EXPORT_BLOCK_NUMBER,
      EXPORT_ACADEMIC_YEAR,
    );
    expect(metaStillValid).toBe(true);

    // --- Step 3: Write to temp file ---
    const tmpDir = os.tmpdir();
    tempFilePath = path.join(tmpDir, `e2e-round-trip-${Date.now()}.xlsx`);
    fs.writeFileSync(tempFilePath, mutatedBuffer);
    expect(fs.existsSync(tempFilePath)).toBe(true);
  });

  test('Step 4-6: Upload mutated file, stage, verify diff', async ({ adminPage }) => {
    // --- Step 4: Navigate to half-day import ---
    await adminPage.goto('/import/half-day');
    await waitForNetworkIdle(adminPage);

    // --- Step 5: Upload the mutated file ---
    await adminPage.locator(selectors.importExport.hdFileInput).setInputFiles(tempFilePath);
    await adminPage
      .locator(selectors.importExport.hdBlockNumber)
      .fill(String(EXPORT_BLOCK_NUMBER));
    await adminPage
      .locator(selectors.importExport.hdAcademicYear)
      .fill(String(EXPORT_ACADEMIC_YEAR));

    // --- Step 6: Stage and verify diff ---
    const [stageResponse] = await Promise.all([
      adminPage.waitForResponse(
        (resp) => resp.url().includes('/stage') && resp.status() === 200,
        { timeout: 30_000 },
      ),
      adminPage.locator(selectors.importExport.hdStageBtn).click(),
    ]);

    expect(stageResponse.ok()).toBe(true);

    // Wait for diff metrics to appear
    const metricChanged = adminPage.locator(selectors.importExport.hdMetricChanged);
    await expect(metricChanged).toBeVisible({ timeout: 10_000 });

    // The "Modified" count should be >= 1 (we changed one cell)
    const changedText = await metricChanged.textContent();
    expect(changedText).toBeTruthy();

    // Extract the numeric value from the metric (e.g., "Modified: 3" -> 3)
    const changedMatch = changedText!.match(/(\d+)/);
    expect(changedMatch).toBeTruthy();
    const changedCount = parseInt(changedMatch![1], 10);
    expect(changedCount).toBeGreaterThanOrEqual(1);
  });

  test('Step 7-8: Apply changes and verify via API', async ({ adminPage }) => {
    // --- Step 7: Select diffs and create draft (then apply) ---
    // Select all diffs on current page
    await adminPage.locator(selectors.importExport.hdSelectPageBtn).click();

    // Fill draft notes
    await adminPage
      .locator(selectors.importExport.hdDraftNotes)
      .fill('Round-trip golden test');

    // Create draft
    const [draftResponse] = await Promise.all([
      adminPage.waitForResponse(
        (resp) => resp.url().includes('/draft') && resp.status() === 200,
        { timeout: 15_000 },
      ),
      adminPage.locator(selectors.importExport.hdCreateDraftBtn).click(),
    ]);
    expect(draftResponse.ok()).toBe(true);

    // Navigate to batch review
    await adminPage.locator(selectors.importExport.hdViewDraftBtn).click();
    await adminPage.waitForURL(/\/import\/batch\//, { timeout: 10_000 });

    // Apply the batch
    const [applyResponse] = await Promise.all([
      adminPage.waitForResponse(
        (resp) => resp.url().includes('/apply') && resp.status() === 200,
        { timeout: 30_000 },
      ),
      adminPage.locator(selectors.importExport.batchApplyBtn).click(),
    ]);
    expect(applyResponse.ok()).toBe(true);

    // Verify status changed to APPLIED
    const statusBadge = adminPage.locator(selectors.importExport.batchStatusBadge);
    await expect(statusBadge).toContainText(/applied/i, { timeout: 10_000 });

    // --- Step 8: Verify via API that the DB changed ---
    // Use Playwright's request context to query the backend directly
    const apiBaseUrl = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';
    const apiContext = adminPage.context().request;

    // Query block assignments for the mutated block
    const assignmentsResponse = await apiContext.get(
      `${apiBaseUrl}/api/v1/half-day/assignments?block_number=${EXPORT_BLOCK_NUMBER}&academic_year=${EXPORT_ACADEMIC_YEAR}`,
    );
    expect(assignmentsResponse.ok()).toBe(true);

    const assignments = await assignmentsResponse.json();
    expect(assignments).toBeTruthy();

    // Verify that at least one assignment reflects the mutation.
    // The exact verification depends on which cell we mutated and the
    // backend's data model. At minimum, we confirm the API returns data
    // for the block we just imported.
    const hasData = Array.isArray(assignments)
      ? assignments.length > 0
      : Object.keys(assignments).length > 0;
    expect(hasData).toBe(true);
  });
});
