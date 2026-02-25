import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';
import { streamToBuffer, parseExportedXlsx } from '../../utils/xlsx-helpers';
import { waitForNetworkIdle } from '../../utils/test-helpers';

/**
 * Export Block E2E Tests
 *
 * Tests the xlsx export pipeline:
 * 1. Navigate to export UI
 * 2. Trigger a block export
 * 3. Intercept the download stream
 * 4. Verify the file is a valid xlsx with __SYS_META__ sheet
 *
 * Prerequisites:
 *   - At least one block with assignments must exist in the database
 *   - Backend export endpoint (/api/v1/half-day/export) must be running
 */

test.describe('Export Block', () => {
  test.beforeEach(async ({ adminPage }) => {
    // Navigate to the import/export hub
    await adminPage.goto('/hub/import-export');
    await waitForNetworkIdle(adminPage);
  });

  test('should display export panel with format options', async ({ adminPage }) => {
    // Verify the export format selectors are visible
    const xlsxOption = adminPage.locator(selectors.importExport.exportFormatXlsx);
    const csvOption = adminPage.locator(selectors.importExport.exportFormatCsv);
    const submitBtn = adminPage.locator(selectors.importExport.exportSubmitBtn);

    await expect(xlsxOption).toBeVisible();
    await expect(csvOption).toBeVisible();
    await expect(submitBtn).toBeVisible();
  });

  test('should download a valid xlsx file when export is triggered', async ({ adminPage }) => {
    // TODO: This test requires at least one block with assignments seeded in the database.
    // Remove test.fixme() once seed data is available.
    test.fixme();

    // Select xlsx format
    await adminPage.locator(selectors.importExport.exportFormatXlsx).click();

    // Trigger download and intercept the download event simultaneously
    const [download] = await Promise.all([
      adminPage.waitForEvent('download'),
      adminPage.locator(selectors.importExport.exportSubmitBtn).click(),
    ]);

    // Verify the download has a filename
    const suggestedFilename = download.suggestedFilename();
    expect(suggestedFilename).toBeTruthy();
    expect(suggestedFilename).toMatch(/\.xlsx$/);

    // Convert the download stream to a buffer
    const readStream = await download.createReadStream();
    expect(readStream).toBeTruthy();
    const buffer = await streamToBuffer(readStream! as unknown as ReadableStream);

    // Verify buffer is non-empty (valid file)
    expect(buffer.length).toBeGreaterThan(0);
  });

  test('should contain __SYS_META__ sheet in exported xlsx', async ({ adminPage }) => {
    // TODO: This test requires seeded block data. Remove test.fixme() once available.
    test.fixme();

    // Select xlsx format and trigger export
    await adminPage.locator(selectors.importExport.exportFormatXlsx).click();

    const [download] = await Promise.all([
      adminPage.waitForEvent('download'),
      adminPage.locator(selectors.importExport.exportSubmitBtn).click(),
    ]);

    const readStream = await download.createReadStream();
    const buffer = await streamToBuffer(readStream! as unknown as ReadableStream);

    // Parse the xlsx and verify __SYS_META__ sheet
    const { meta, sheetName, rows } = await parseExportedXlsx(buffer);

    expect(meta).not.toBeNull();
    expect(meta!.academic_year).toBeDefined(); // @enum-ok
    expect(sheetName).toBeTruthy();

    // The visible schedule sheet should have at least a header structure
    // (rows may be empty if no assignments, but sheetName must exist)
    expect(typeof sheetName).toBe('string');
  });

  test('should export valid schedule rows from populated block', async ({ adminPage }) => {
    // TODO: Requires a block with resident assignments. Remove test.fixme() once seeded.
    test.fixme();

    await adminPage.locator(selectors.importExport.exportFormatXlsx).click();

    const [download] = await Promise.all([
      adminPage.waitForEvent('download'),
      adminPage.locator(selectors.importExport.exportSubmitBtn).click(),
    ]);

    const readStream = await download.createReadStream();
    const buffer = await streamToBuffer(readStream! as unknown as ReadableStream);

    const { rows } = await parseExportedXlsx(buffer);

    // With seeded data, we expect at least one schedule row
    expect(rows.length).toBeGreaterThan(0);

    // Each row should have a name and day values
    for (const row of rows) {
      expect(row.name).toBeTruthy();
      expect(row.days.length).toBeGreaterThan(0);
    }
  });
});
