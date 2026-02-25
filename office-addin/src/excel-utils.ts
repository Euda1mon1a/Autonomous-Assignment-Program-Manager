import { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';

const PROTECTED_SHEETS = ["__ANCHORS__", "__REF__", "__SYS_META__"];

function assertWritable(sheetName: string): void {
  if (PROTECTED_SHEETS.includes(sheetName)) {
    throw new Error(`Write refused: ${sheetName} is a protected metadata sheet`);
  }
}

const MAX_ROW = 500;
const MAX_COL = 100;

export async function writeScheduleCell(
  sheetName: string,
  row: number,
  col: number,
  value: string
) {
  return Excel.run(async (context) => {
    assertWritable(sheetName);

    // Bounds validation — prevents LLM-directed writes to arbitrary cells
    if (!Number.isInteger(row) || !Number.isInteger(col) || row < 1 || col < 1 || row > MAX_ROW || col > MAX_COL) {
      throw new Error(`Write refused: row=${row}, col=${col} is out of bounds (max ${MAX_ROW}x${MAX_COL})`);
    }

    const sheet = context.workbook.worksheets.getItem(sheetName);

    // Excel ranges are 0-indexed for getCell
    sheet.getCell(row - 1, col - 1).values = [[value]];

    // Auto-clear hash in __ANCHORS__ for this row
    try {
      const anchors = context.workbook.worksheets.getItem("__ANCHORS__");
      anchors.getCell(row - 1, 2).values = [[""]];
    } catch (e) {
      console.warn("Could not clear hash in __ANCHORS__ sheet", e);
    }

    await context.sync();
  });
}

export interface BlockMetadata {
  academic_year: number;
  block_number: number;
  export_timestamp: string;
  export_version: number;
  llm_rules_of_engagement?: string;
}

export async function readSysMeta(): Promise<BlockMetadata | null> {
  return Excel.run(async (context) => {
    try {
      const sheet = context.workbook.worksheets.getItem("__SYS_META__");
      const cell = sheet.getCell(0, 0); // A1
      cell.load("values");
      await context.sync();

      const jsonStr = cell.values[0][0];
      if (typeof jsonStr === 'string' && jsonStr) {
        return JSON.parse(jsonStr) as BlockMetadata;
      }
      return null;
    } catch (error) {
      console.warn("Could not read __SYS_META__", error);
      return null;
    }
  });
}

export async function readRefData(): Promise<{rotations: string[], activities: string[]}> {
  return Excel.run(async (context) => {
    try {
      const sheet = context.workbook.worksheets.getItem("__REF__");
      const usedRange = sheet.getUsedRange();
      usedRange.load("values");
      await context.sync();

      const rotations: string[] = [];
      const activities: string[] = [];

      for (let i = 1; i < usedRange.values.length; i++) {
        if (usedRange.values[i][0]) rotations.push(usedRange.values[i][0]);
        if (usedRange.values[i][1]) activities.push(usedRange.values[i][1]);
      }
      return { rotations, activities };
    } catch (e) {
      console.warn("Could not read __REF__", e);
      return { rotations: [], activities: [] };
    }
  });
}

export async function getVisibleGridSnapshot(): Promise<any[][]> {
  return Excel.run(async (context) => {
    try {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      const usedRange = sheet.getUsedRange();
      usedRange.load("values");
      await context.sync();
      return usedRange.values;
    } catch (e) {
      console.warn("Could not read active worksheet", e);
      return [];
    }
  });
}

export async function getActiveSheetName(): Promise<string> {
  return Excel.run(async (context) => {
    const sheet = context.workbook.worksheets.getActiveWorksheet();
    sheet.load("name");
    await context.sync();
    return sheet.name;
  });
}
