/**
 * Types for FMIT block schedule import
 *
 * Maps to backend schemas in backend/app/schemas/block_import.py
 */

// ============================================================================
// Resident Roster Types
// ============================================================================

/**
 * Single resident in parsed roster
 */
export interface ResidentRosterItem {
  /** Resident name (Last, First format) */
  name: string;
  /** Rotation template (R1, R2, R3, etc.) */
  template: string;
  /** PGY level (PGY 1, PGY 2, PGY 3, FAC) */
  role: string;
  /** Row number in source spreadsheet */
  row: number;
  /** Name match confidence (0.0-1.0) */
  confidence: number;
}

// ============================================================================
// FMIT Schedule Types
// ============================================================================

/**
 * FMIT attending assignment for a single week
 */
export interface ParsedFMITWeek {
  /** Block number (1-13) */
  block_number: number;
  /** Week within block (1-4) */
  week_number: number;
  /** Week start date (ISO format) */
  start_date: string | null;
  /** Week end date (ISO format) */
  end_date: string | null;
  /** Assigned faculty name */
  faculty_name: string;
  /** True if holiday call week */
  is_holiday_call: boolean;
}

// ============================================================================
// Assignment Types
// ============================================================================

/**
 * Single daily assignment extracted from block schedule
 */
export interface ParsedBlockAssignment {
  /** Person name */
  person_name: string;
  /** Assignment date (ISO format) */
  date: string;
  /** Rotation template */
  template: string;
  /** Person role/PGY level */
  role: string;
  /** AM slot value */
  slot_am: string | null;
  /** PM slot value */
  slot_pm: string | null;
  /** Source row in spreadsheet */
  row_idx: number;
  /** Name match confidence */
  confidence: number;
}

// ============================================================================
// Block Parse Response
// ============================================================================

/**
 * Full response from block schedule parsing endpoint
 */
export interface BlockParseResponse {
  /** True if parsing succeeded without errors */
  success: boolean;
  /** Block number parsed */
  block_number: number;
  /** Block start date (ISO format) */
  start_date: string | null;
  /** Block end date (ISO format) */
  end_date: string | null;
  /** All parsed residents */
  residents: ResidentRosterItem[];
  /** Residents grouped by template */
  residents_by_template: Record<string, ResidentRosterItem[]>;
  /** FMIT weekly assignments */
  fmit_schedule: ParsedFMITWeek[];
  /** Daily assignments (AM/PM slots) */
  assignments: ParsedBlockAssignment[];
  /** Parsing warnings (low confidence matches) */
  warnings: string[];
  /** Parsing errors */
  errors: string[];
  /** Total resident count */
  total_residents: number;
  /** Total assignment count */
  total_assignments: number;
}

// ============================================================================
// Import Request Types
// ============================================================================

/**
 * Parameters for parsing a block schedule
 */
export interface BlockParseRequest {
  /** Block number to parse (1-13) */
  blockNumber: number;
  /** Optional list of known person names for fuzzy matching */
  knownPeople?: string[];
  /** Whether to include FMIT schedule (default: true) */
  includeFmit?: boolean;
}

// ============================================================================
// Import State Types
// ============================================================================

/**
 * Status of the FMIT import process
 */
export type FmitImportStatus =
  | 'idle'
  | 'uploading'
  | 'parsing'
  | 'preview'
  | 'error';

/**
 * State for FMIT import workflow
 */
export interface FmitImportState {
  status: FmitImportStatus;
  file: File | null;
  blockNumber: number;
  includeFmit: boolean;
  parseResult: BlockParseResponse | null;
  error: string | null;
}
