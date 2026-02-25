/**
 * Xlsx helpers for Playwright E2E tests.
 *
 * Uses xlsx-populate (not exceljs/openpyxl) because it preserves
 * veryHidden sheets like __SYS_META__ on round-trip — critical for
 * stateful import/export testing.
 */

import XlsxPopulate from 'xlsx-populate';

/** Shape of the JSON blob stored in __SYS_META__ cell A1. */
interface SysMetadata {
  academic_year: number; // @enum-ok — raw JSON value, not an object key
  block_number?: number | null;
  export_version?: number;
  export_timestamp?: string;
  block_map?: Record<string, string>;
  llm_rules_of_engagement?: string;
}

/** A single schedule row extracted from the visible sheet. */
interface ScheduleRow {
  /** Row index in the sheet (1-based). */
  row: number;
  /** Resident/faculty name from column E. */
  name: string;
  /** Day-indexed values from columns F onward. */
  days: (string | number | null)[];
}

/**
 * Parse an exported xlsx buffer.
 *
 * Reads the __SYS_META__ sheet (cell A1 as JSON) and extracts schedule
 * rows from the first visible sheet. Rows 9-69, column E = names,
 * columns F+ = schedule data per the Block Template2 format.
 */
export async function parseExportedXlsx(buffer: Buffer): Promise<{
  meta: SysMetadata | null;
  rows: ScheduleRow[];
  sheetName: string;
}> {
  const workbook = await XlsxPopulate.fromDataAsync(buffer);

  // --- Read __SYS_META__ ---
  let meta: SysMetadata | null = null;
  const metaSheet = workbook.sheet('__SYS_META__');
  if (metaSheet) {
    const raw = metaSheet.cell('A1').value();
    if (typeof raw === 'string') {
      try {
        meta = JSON.parse(raw) as SysMetadata;
      } catch {
        // Malformed JSON — leave meta null
      }
    }
  }

  // --- Find first visible sheet ---
  const visibleSheet = workbook.sheets().find((s) => !s.hidden());
  if (!visibleSheet) {
    return { meta, rows: [], sheetName: '' };
  }

  // --- Extract schedule rows (Block Template2: rows 9-69, col E = name, F+ = days) ---
  const rows: ScheduleRow[] = [];
  const NAME_COL = 5; // Column E (1-based)
  const FIRST_DAY_COL = 6; // Column F
  const START_ROW = 9;
  const END_ROW = 69;

  for (let r = START_ROW; r <= END_ROW; r++) {
    const nameVal = visibleSheet.cell(r, NAME_COL).value();
    const name = nameVal != null ? String(nameVal).trim() : '';
    if (!name) continue;

    const days: (string | number | null)[] = [];
    // Read columns F through the last used column (up to ~37 days max for a block)
    for (let c = FIRST_DAY_COL; c <= FIRST_DAY_COL + 36; c++) {
      const val = visibleSheet.cell(r, c).value();
      if (val === undefined || val === null) {
        days.push(null);
      } else {
        days.push(typeof val === 'number' ? val : String(val));
      }
    }

    rows.push({ row: r, name, days });
  }

  return { meta, rows, sheetName: visibleSheet.name() };
}

/**
 * Mutate a single cell in an xlsx buffer and return the modified buffer.
 *
 * Uses xlsx-populate which preserves veryHidden sheets and formatting.
 */
export async function mutateXlsxCell(
  buffer: Buffer,
  sheetName: string,
  cellRef: string,
  newValue: string,
): Promise<Buffer> {
  const workbook = await XlsxPopulate.fromDataAsync(buffer);
  const sheet = workbook.sheet(sheetName);
  if (!sheet) {
    throw new Error(`Sheet "${sheetName}" not found in workbook`);
  }
  sheet.cell(cellRef).value(newValue);
  const output = await workbook.outputAsync();
  return Buffer.from(output as ArrayBuffer);
}

/**
 * Verify that the __SYS_META__ sheet exists and contains the expected
 * block_number and academic_year.
 */
export async function verifySysMeta(
  buffer: Buffer,
  expectedBlock: number,
  expectedYear: number,
): Promise<boolean> {
  const workbook = await XlsxPopulate.fromDataAsync(buffer);
  const metaSheet = workbook.sheet('__SYS_META__');
  if (!metaSheet) return false;

  const raw = metaSheet.cell('A1').value();
  if (typeof raw !== 'string') return false;

  try {
    const meta = JSON.parse(raw) as SysMetadata;
    return meta.block_number === expectedBlock && meta.academic_year === expectedYear;
  } catch {
    return false;
  }
}

/**
 * Convert a ReadableStream (e.g. from a Playwright download) to a Buffer.
 */
export async function streamToBuffer(stream: ReadableStream): Promise<Buffer> {
  const reader = stream.getReader();
  const chunks: Uint8Array[] = [];

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }

  return Buffer.concat(chunks);
}
