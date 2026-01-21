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
  pgyLevel?: number;
  performsProcedures?: boolean;
  specialties?: string;
  primaryDuty?: string;
}

/**
 * Standard column mappings for assignment imports
 */
export interface AssignmentImportRow {
  personName: string;
  personId?: string;
  date: string;
  timeOfDay: 'AM' | 'PM';
  rotationName?: string;
  rotationTemplateId?: string;
  role: 'primary' | 'supervising' | 'backup';
  activityOverride?: string;
  notes?: string;
}

/**
 * Standard column mappings for absence imports
 */
export interface AbsenceImportRow {
  personName: string;
  personId?: string;
  startDate: string;
  endDate: string;
  absenceType: 'vacation' | 'deployment' | 'tdy' | 'medical' | 'family_emergency' | 'conference' | 'sick' | 'bereavement' | 'emergency_leave' | 'convalescent' | 'maternity_paternity' | 'personal' | 'training' | 'military_duty';
  deploymentOrders?: boolean;
  tdyLocation?: string;
  replacementActivity?: string;
  notes?: string;
}

/**
 * Standard column mappings for schedule imports (bulk assignments)
 */
export interface ScheduleImportRow {
  date: string;
  timeOfDay: 'AM' | 'PM';
  personName: string;
  personId?: string;
  rotationName?: string;
  rotationTemplateId?: string;
  role: 'primary' | 'supervising' | 'backup';
  activityOverride?: string;
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
