/**
 * Types for bulk import/export functionality
 */

import type { Person, Assignment, Absence, RotationTemplate } from '@/types/api';

// ============================================================================
// Import Types
// ============================================================================

/**
 * Supported import data types
 */
export type ImportDataType = 'assignments' | 'people' | 'absences' | 'schedules';

/**
 * Supported file formats for import
 */
export type ImportFileFormat = 'csv' | 'xlsx' | 'json';

/**
 * Import validation error
 */
export interface ImportValidationError {
  row: number;
  column: string;
  value: unknown;
  message: string;
  severity: 'error' | 'warning';
}

/**
 * Import row status after validation
 */
export type ImportRowStatus = 'valid' | 'warning' | 'error' | 'skipped';

/**
 * A single row in the import preview
 */
export interface ImportPreviewRow<T = Record<string, unknown>> {
  rowNumber: number;
  data: T;
  status: ImportRowStatus;
  errors: ImportValidationError[];
  warnings: ImportValidationError[];
}

/**
 * Import preview result after parsing and validation
 */
export interface ImportPreviewResult<T = Record<string, unknown>> {
  totalRows: number;
  validRows: number;
  errorRows: number;
  warningRows: number;
  skippedRows: number;
  rows: ImportPreviewRow<T>[];
  columns: string[];
  detectedFormat: ImportFileFormat;
  dataType: ImportDataType;
}

/**
 * Import progress state
 */
export interface ImportProgress {
  status: 'idle' | 'parsing' | 'validating' | 'importing' | 'complete' | 'error';
  currentRow: number;
  totalRows: number;
  processedRows: number;
  successCount: number;
  errorCount: number;
  warningCount: number;
  message: string;
  errors: ImportValidationError[];
}

/**
 * Import options configuration
 */
export interface ImportOptions {
  skipDuplicates: boolean;
  updateExisting: boolean;
  skipInvalidRows: boolean;
  dateFormat: string;
  trimWhitespace: boolean;
}

/**
 * Import result after completion
 */
export interface ImportResult {
  success: boolean;
  totalProcessed: number;
  successCount: number;
  errorCount: number;
  skippedCount: number;
  errors: ImportValidationError[];
  importedIds: string[];
}

// ============================================================================
// Export Types
// ============================================================================

/**
 * Supported export formats
 */
export type ExportFormat = 'csv' | 'xlsx' | 'pdf' | 'json';

/**
 * Export column configuration
 */
export interface ExportColumn {
  key: string;
  header: string;
  width?: number;
  format?: (value: unknown) => string;
}

/**
 * Export options configuration
 */
export interface ExportOptions {
  format: ExportFormat;
  filename: string;
  columns: ExportColumn[];
  includeHeaders: boolean;
  dateFormat: string;
  title?: string;
  subtitle?: string;
}

/**
 * Export progress state
 */
export interface ExportProgress {
  status: 'idle' | 'preparing' | 'generating' | 'complete' | 'error';
  currentRow: number;
  totalRows: number;
  message: string;
}

// ============================================================================
// Column Mappings
// ============================================================================

/**
 * Standard column mappings for person imports
 */
export interface PersonImportRow {
  name: string;
  email?: string;
  type: 'resident' | 'faculty';
  pgy_level?: number;
  performs_procedures?: boolean;
  specialties?: string;
  primary_duty?: string;
}

/**
 * Standard column mappings for assignment imports
 */
export interface AssignmentImportRow {
  person_name: string;
  person_id?: string;
  date: string;
  time_of_day: 'AM' | 'PM';
  rotation_name?: string;
  rotation_template_id?: string;
  role: 'primary' | 'supervising' | 'backup';
  activity_override?: string;
  notes?: string;
}

/**
 * Standard column mappings for absence imports
 */
export interface AbsenceImportRow {
  person_name: string;
  person_id?: string;
  start_date: string;
  end_date: string;
  absence_type: 'vacation' | 'deployment' | 'tdy' | 'medical' | 'family_emergency' | 'conference';
  deployment_orders?: boolean;
  tdy_location?: string;
  replacement_activity?: string;
  notes?: string;
}

/**
 * Standard column mappings for schedule imports (bulk assignments)
 */
export interface ScheduleImportRow {
  date: string;
  time_of_day: 'AM' | 'PM';
  person_name: string;
  person_id?: string;
  rotation_name?: string;
  rotation_template_id?: string;
  role: 'primary' | 'supervising' | 'backup';
  activity_override?: string;
}

// ============================================================================
// Data Type Maps
// ============================================================================

export type ImportDataMap = {
  people: PersonImportRow;
  assignments: AssignmentImportRow;
  absences: AbsenceImportRow;
  schedules: ScheduleImportRow;
};

export type ExportDataMap = {
  people: Person;
  assignments: Assignment;
  absences: Absence;
  schedules: Assignment;
  rotationTemplates: RotationTemplate;
};

// ============================================================================
// File Drop Zone
// ============================================================================

export interface FileDropState {
  isDragging: boolean;
  file: File | null;
  error: string | null;
}
