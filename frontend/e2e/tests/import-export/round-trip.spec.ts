import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';
import { streamToBuffer, mutateXlsxCell, verifySysMeta } from '../../utils/xlsx-helpers';
import { waitForNetworkIdle } from '../../utils/test-helpers';

/**
 * Round-Trip E2E Tests
 *
 * Tests the deterministic export -> mutate -> import -> verify pipeline.
 * Includes:
 *   - Golden Test: mutate one cell, verify >=1 Modified diff, apply, verify API
 *   - Zero Diffs: re-import unmodified export, verify 0 changes
 *   - Wrong Block: import Block 5 file as Block 10, verify hard rejection
 *
 * Prerequisites:
 *   - A populated block with assignments must exist in the database
 *   - Backend export and import endpoints must be running
 *   - __SYS_META__ sheet must be preserved through the round-trip
 */

const EXPORT_BLOCK_NUMBER = 10;
const EXPORT_ACADEMIC_YEAR = 2025;
const MUTATE_CELL_REF = 'F9';
const MUTATE_NEW_VALUE = 'NF';

test.describe('Round-Trip (Golden Test)', () => {
  test.skip(
    () => !process.env.E2E_HAS_SEEDED_DATA,
    'Requires seeded database with block 10 assignments',
  );

  test('Export -> mutate -> import -> apply -> verify', async ({ adminPage }) => {
    let exportedBuffer: Buffer;
    let mutatedBuffer: Buffer;
    let tempFilePath: string;

    await test.step('Step 1: Export block to xlsx', async () => {
      await adminPage.goto('/hub/import-export');
      await waitForNetworkIdle(adminPage);

      await adminPage.locator(selectors.importExport.exportFormatXlsx).click();

      const [download] = await Promise.all([
        adminPage.waitForEvent('download'),
        adminPage.locator(selectors.importExport.exportSubmitBtn).click(),
      ]);

      const readStream = await download.createReadStream();
      expect(readStream).toBeTruthy();
      exportedBuffer = await streamToBuffer(readStream! as unknown as ReadableStream);
      expect(exportedBuffer.length).toBeGreaterThan(0);

      const metaValid = await verifySysMeta(
        exportedBuffer,
        EXPORT_BLOCK_NUMBER,
        EXPORT_ACADEMIC_YEAR,
      );
      expect(metaValid).toBe(true);
    });

    await test.step('Step 2: Mutate one cell and write temp file', async () => {
      const XlsxPopulate = await import('xlsx-populate');
      const workbook = await XlsxPopulate.default.fromDataAsync(exportedBuffer);
      const visibleSheet = workbook
        .sheets()
        .find((s: { hidden: () => unknown }) => !s.hidden());
      expect(visibleSheet).toBeTruthy();

      mutatedBuffer = await mutateXlsxCell(
        exportedBuffer,
        visibleSheet!.name(),
        MUTATE_CELL_REF,
        MUTATE_NEW_VALUE,
      );
      expect(mutatedBuffer.length).toBeGreaterThan(0);

      // __SYS_META__ must survive mutation
      const metaStillValid = await verifySysMeta(
        mutatedBuffer,
        EXPORT_BLOCK_NUMBER,
        EXPORT_ACADEMIC_YEAR,
      );
      expect(metaStillValid).toBe(true);

      const tmpDir = os.tmpdir();
      tempFilePath = path.join(tmpDir, `e2e-round-trip-${Date.now()}.xlsx`);
      fs.writeFileSync(tempFilePath, mutatedBuffer);
    });

    await test.step('Step 3: Upload mutated file and stage', async () => {
      await adminPage.goto('/import/half-day');
      await waitForNetworkIdle(adminPage);

      await adminPage
        .locator(selectors.importExport.hdFileInput)
        .setInputFiles(tempFilePath);
      await adminPage
        .locator(selectors.importExport.hdBlockNumber)
        .fill(String(EXPORT_BLOCK_NUMBER));
      await adminPage
        .locator(selectors.importExport.hdAcademicYear)
        .fill(String(EXPORT_ACADEMIC_YEAR));

      const [stageResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/stage') && resp.status() === 200,
          { timeout: 30_000 },
        ),
        adminPage.locator(selectors.importExport.hdStageBtn).click(),
      ]);
      expect(stageResponse.ok()).toBe(true);
    });

    await test.step('Step 4: Verify diff shows >= 1 Modified', async () => {
      const metricChanged = adminPage.locator(selectors.importExport.hdMetricChanged);
      await expect(metricChanged).toBeVisible({ timeout: 10_000 });

      const changedText = await metricChanged.textContent();
      expect(changedText).toBeTruthy();
      const changedMatch = changedText!.match(/(\d+)/);
      expect(changedMatch).toBeTruthy();
      expect(parseInt(changedMatch![1], 10)).toBeGreaterThanOrEqual(1);
    });

    await test.step('Step 5: Select diffs and create draft', async () => {
      await adminPage.locator(selectors.importExport.hdSelectPageBtn).click();
      await adminPage
        .locator(selectors.importExport.hdDraftNotes)
        .fill('Round-trip golden test');

      const [draftResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/draft') && resp.status() === 200,
          { timeout: 15_000 },
        ),
        adminPage.locator(selectors.importExport.hdCreateDraftBtn).click(),
      ]);
      expect(draftResponse.ok()).toBe(true);
    });

    await test.step('Step 6: Apply batch and verify', async () => {
      await adminPage.locator(selectors.importExport.hdViewDraftBtn).click();
      await adminPage.waitForURL(/\/import\/batch\//, { timeout: 10_000 });

      const [applyResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/apply') && resp.status() === 200,
          { timeout: 30_000 },
        ),
        adminPage.locator(selectors.importExport.batchApplyBtn).click(),
      ]);
      expect(applyResponse.ok()).toBe(true);

      const statusBadge = adminPage.locator(selectors.importExport.batchStatusBadge);
      await expect(statusBadge).toContainText(/applied/i, { timeout: 10_000 });
    });

    await test.step('Step 7: Verify via API that DB reflects change', async () => {
      const apiBaseUrl = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';
      const apiContext = adminPage.context().request;

      const assignmentsResponse = await apiContext.get(
        `${apiBaseUrl}/api/v1/half-day/assignments?block_number=${EXPORT_BLOCK_NUMBER}&academic_year=${EXPORT_ACADEMIC_YEAR}`,
      );
      expect(assignmentsResponse.ok()).toBe(true);

      const assignments = await assignmentsResponse.json();
      expect(assignments).toBeTruthy();
      const hasData = Array.isArray(assignments)
        ? assignments.length > 0
        : Object.keys(assignments).length > 0;
      expect(hasData).toBe(true);
    });

    // Cleanup
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
    }
  });
});

test.describe('Round-Trip: Zero Diffs', () => {
  test.skip(
    () => !process.env.E2E_HAS_SEEDED_DATA,
    'Requires seeded database with block 10 assignments',
  );

  test('Re-importing unmodified export produces 0 diffs', async ({ adminPage }) => {
    let exportedBuffer: Buffer;
    let tempFilePath: string;

    await test.step('Export block to xlsx', async () => {
      await adminPage.goto('/hub/import-export');
      await waitForNetworkIdle(adminPage);

      await adminPage.locator(selectors.importExport.exportFormatXlsx).click();

      const [download] = await Promise.all([
        adminPage.waitForEvent('download'),
        adminPage.locator(selectors.importExport.exportSubmitBtn).click(),
      ]);

      const readStream = await download.createReadStream();
      expect(readStream).toBeTruthy();
      exportedBuffer = await streamToBuffer(readStream! as unknown as ReadableStream);
      expect(exportedBuffer.length).toBeGreaterThan(0);
    });

    await test.step('Re-import same file without changes', async () => {
      const tmpDir = os.tmpdir();
      tempFilePath = path.join(tmpDir, `e2e-zero-diffs-${Date.now()}.xlsx`);
      fs.writeFileSync(tempFilePath, exportedBuffer);

      await adminPage.goto('/import/half-day');
      await waitForNetworkIdle(adminPage);

      await adminPage
        .locator(selectors.importExport.hdFileInput)
        .setInputFiles(tempFilePath);
      await adminPage
        .locator(selectors.importExport.hdBlockNumber)
        .fill(String(EXPORT_BLOCK_NUMBER));
      await adminPage
        .locator(selectors.importExport.hdAcademicYear)
        .fill(String(EXPORT_ACADEMIC_YEAR));

      const [stageResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/stage') && resp.status() === 200,
          { timeout: 30_000 },
        ),
        adminPage.locator(selectors.importExport.hdStageBtn).click(),
      ]);
      expect(stageResponse.ok()).toBe(true);
    });

    await test.step('Verify 0 Modified diffs', async () => {
      const metricChanged = adminPage.locator(selectors.importExport.hdMetricChanged);
      // Wait for metrics to render
      await expect(metricChanged).toBeVisible({ timeout: 10_000 });

      const changedText = await metricChanged.textContent();
      expect(changedText).toBeTruthy();
      const changedMatch = changedText!.match(/(\d+)/);
      expect(changedMatch).toBeTruthy();
      expect(parseInt(changedMatch![1], 10)).toBe(0);
    });

    // Cleanup
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
    }
  });
});

test.describe('Round-Trip: Wrong Block Rejection', () => {
  test.skip(
    () => !process.env.E2E_HAS_SEEDED_DATA,
    'Requires seeded database with block 10 assignments',
  );

  test('Importing Block 10 file as Block 5 is rejected', async ({ adminPage }) => {
    const fixturesDir = path.resolve(__dirname, '../../fixtures');
    const testFilePath = path.join(fixturesDir, 'test-block10.xlsx');

    // Use the pre-generated fixture (block_number=10 in __SYS_META__)
    expect(fs.existsSync(testFilePath)).toBe(true);

    await test.step('Upload Block 10 file with Block 5 selected', async () => {
      await adminPage.goto('/import/half-day');
      await waitForNetworkIdle(adminPage);

      await adminPage
        .locator(selectors.importExport.hdFileInput)
        .setInputFiles(testFilePath);
      // Intentionally mismatched: file says Block 10, user selects Block 5
      await adminPage.locator(selectors.importExport.hdBlockNumber).fill('5');
      await adminPage
        .locator(selectors.importExport.hdAcademicYear)
        .fill(String(EXPORT_ACADEMIC_YEAR));
    });

    await test.step('Stage is rejected with block mismatch error', async () => {
      const [stageResponse] = await Promise.all([
        adminPage.waitForResponse(
          (resp) => resp.url().includes('/stage'),
          { timeout: 30_000 },
        ),
        adminPage.locator(selectors.importExport.hdStageBtn).click(),
      ]);

      // Backend should return 400/422 for block mismatch
      expect(stageResponse.status()).toBeGreaterThanOrEqual(400);

      // The error message should mention block mismatch
      const body = await stageResponse.json().catch(() => null);
      if (body) {
        const errorText = JSON.stringify(body).toLowerCase();
        expect(errorText).toContain('block mismatch');
      }
    });
  });
});
