/**
 * Synthetic Excel fixture generator for E2E tests.
 *
 * Generates two xlsx files in Block Template2 format:
 * - test-block10.xlsx — Valid block schedule with 5 residents
 * - test-acgme-violation.xlsx — Same format, Resident 1 has 7 consecutive NF (1-in-7 violation)
 *
 * Uses xlsx-populate to preserve veryHidden sheets (__SYS_META__) on round-trip.
 *
 * Usage:
 *   npx tsx e2e/fixtures/generate-test-xlsx.ts
 */

import XlsxPopulate from 'xlsx-populate';
import * as path from 'path';
import * as fs from 'fs';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const FIXTURES_DIR = __dirname;
const BLOCK_START_DATE = new Date(2025, 2, 10); // March 10, 2025
const NUM_DAYS = 28;
const BLOCK_NUMBER = 10;
const ACADEMIC_YEAR = 2025;

const RESIDENTS = [
  { name: 'Test Resident 1', pgy: 2 },
  { name: 'Test Resident 2', pgy: 3 },
  { name: 'Test Resident 3', pgy: 1 },
  { name: 'Test Resident 4', pgy: 2 },
  { name: 'Test Resident 5', pgy: 3 },
];

const ACTIVITY_CODES = ['C', 'NF', 'FMIT-PG', 'LV-AM', 'ADMIN'];

const ACTIVITY_REF = [
  { code: 'C', description: 'Clinic' },
  { code: 'NF', description: 'Night Float' },
  { code: 'FMIT-PG', description: 'FMIT Postgraduate' },
  { code: 'LV-AM', description: 'Leave AM' },
  { code: 'ADMIN', description: 'Administrative' },
  { code: 'DERM-PG', description: 'Dermatology Postgraduate' },
  { code: 'CARDS-NF', description: 'Cardiology Night Float' },
  { code: 'ER', description: 'Emergency Room' },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function addDays(d: Date, n: number): Date {
  const result = new Date(d);
  result.setDate(result.getDate() + n);
  return result;
}

function formatDateHeader(d: Date): string {
  return `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear()}`;
}

// ---------------------------------------------------------------------------
// Workbook Builder
// ---------------------------------------------------------------------------

async function createBlockWorkbook(violation: boolean): Promise<Buffer> {
  const workbook = await XlsxPopulate.fromBlankAsync();

  // -- Visible schedule sheet --
  const sheet = workbook.sheet(0);
  sheet.name(`Block ${BLOCK_NUMBER}`);

  // Row 3: date headers (col F onward)
  for (let d = 0; d < NUM_DAYS; d++) {
    sheet.cell(3, 6 + d).value(formatDateHeader(addDays(BLOCK_START_DATE, d)));
  }

  // Row 8: column headers
  sheet.cell(8, 4).value('PGY');
  sheet.cell(8, 5).value('Name');
  for (let d = 0; d < NUM_DAYS; d++) {
    sheet.cell(8, 6 + d).value(formatDateHeader(addDays(BLOCK_START_DATE, d)));
  }

  // Rows 9-13: resident schedule data
  for (let i = 0; i < RESIDENTS.length; i++) {
    const row = 9 + i;
    const resident = RESIDENTS[i];

    sheet.cell(row, 4).value(resident.pgy);
    sheet.cell(row, 5).value(resident.name); // Col E = name (parser reads this)

    for (let d = 0; d < NUM_DAYS; d++) {
      let code: string;

      if (violation && i === 0) {
        // Resident 1: NF for 7 consecutive days (violates 1-in-7), then C
        code = d < 7 ? 'NF' : 'C';
      } else {
        // Deterministic rotation: each resident offset by their index
        code = ACTIVITY_CODES[(i + d) % ACTIVITY_CODES.length];
      }

      sheet.cell(row, 6 + d).value(code); // Col F+ = day values
    }
  }

  // -- __SYS_META__ sheet (veryHidden) --
  const metaSheet = workbook.addSheet('__SYS_META__');
  metaSheet.hidden('veryHidden');

  const metaPayload = {
    block_number: BLOCK_NUMBER,
    academic_year: ACADEMIC_YEAR,
    export_version: 1,
    export_timestamp: '2025-03-01T00:00:00Z',
  };
  metaSheet.cell('A1').value(JSON.stringify(metaPayload));

  // -- __REF__ sheet (activity code reference) --
  const refSheet = workbook.addSheet('__REF__');
  refSheet.cell('A1').value('Code');
  refSheet.cell('B1').value('Description');
  ACTIVITY_REF.forEach((ref, i) => {
    refSheet.cell(`A${i + 2}`).value(ref.code);
    refSheet.cell(`B${i + 2}`).value(ref.description);
  });

  const output = await workbook.outputAsync();
  return Buffer.from(output as ArrayBuffer);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  console.log('Generating test fixtures...');

  // test-block10.xlsx — valid block schedule
  const validBuffer = await createBlockWorkbook(false);
  const validPath = path.join(FIXTURES_DIR, 'test-block10.xlsx');
  fs.writeFileSync(validPath, validBuffer);
  console.log(`  Created ${validPath}`);

  // test-acgme-violation.xlsx — 1-in-7 violation
  const violationBuffer = await createBlockWorkbook(true);
  const violationPath = path.join(FIXTURES_DIR, 'test-acgme-violation.xlsx');
  fs.writeFileSync(violationPath, violationBuffer);
  console.log(`  Created ${violationPath}`);

  console.log('Done.');
}

main().catch((err) => {
  console.error('Failed to generate fixtures:', err);
  process.exit(1);
});
