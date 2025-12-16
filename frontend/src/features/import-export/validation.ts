/**
 * Validation functions for import data
 */

import type {
  ImportDataType,
  ImportValidationError,
  ImportPreviewRow,
  ImportPreviewResult,
  PersonImportRow,
  AssignmentImportRow,
  AbsenceImportRow,
  ScheduleImportRow,
} from './types';

import {
  validateRequiredFields,
  validateEnum,
  validateEmail,
  validateDateFormat,
  validateNumericRange,
  parseDate,
} from './utils';

// ============================================================================
// Validation Configurations
// ============================================================================

const PERSON_TYPES = ['resident', 'faculty'];
const ABSENCE_TYPES = ['vacation', 'deployment', 'tdy', 'medical', 'family_emergency', 'conference'];
const ASSIGNMENT_ROLES = ['primary', 'supervising', 'backup'];
const TIME_OF_DAY = ['AM', 'PM'];

// ============================================================================
// People Validation
// ============================================================================

/**
 * Validate a person import row
 */
export function validatePersonRow(
  row: Record<string, unknown>,
  rowNumber: number
): ImportValidationError[] {
  const errors: ImportValidationError[] = [];

  // Required fields
  errors.push(...validateRequiredFields(row, ['name', 'type'], rowNumber));

  // Type validation
  const typeError = validateEnum(row.type, PERSON_TYPES, 'type', rowNumber);
  if (typeError) errors.push(typeError);

  // Email validation (optional but must be valid if provided)
  const emailError = validateEmail(row.email, 'email', rowNumber);
  if (emailError) errors.push(emailError);

  // PGY level validation for residents
  if (row.type === 'resident' && row.pgy_level !== null && row.pgy_level !== undefined) {
    const pgyError = validateNumericRange(row.pgy_level, 'pgy_level', 1, 8, rowNumber);
    if (pgyError) errors.push(pgyError);
  }

  // Name minimum length
  if (row.name && String(row.name).trim().length < 2) {
    errors.push({
      row: rowNumber,
      column: 'name',
      value: row.name,
      message: 'Name must be at least 2 characters',
      severity: 'error',
    });
  }

  return errors;
}

// ============================================================================
// Assignment Validation
// ============================================================================

/**
 * Validate an assignment import row
 */
export function validateAssignmentRow(
  row: Record<string, unknown>,
  rowNumber: number
): ImportValidationError[] {
  const errors: ImportValidationError[] = [];

  // Required fields - need either person_name or person_id
  if (!row.person_name && !row.person_id) {
    errors.push({
      row: rowNumber,
      column: 'person_name',
      value: row.person_name,
      message: 'Either person_name or person_id is required',
      severity: 'error',
    });
  }

  // Required fields
  errors.push(...validateRequiredFields(row, ['date', 'time_of_day', 'role'], rowNumber));

  // Date validation
  const dateError = validateDateFormat(row.date, 'date', rowNumber);
  if (dateError) errors.push(dateError);

  // Time of day validation
  const timeError = validateEnum(row.time_of_day, TIME_OF_DAY, 'time_of_day', rowNumber);
  if (timeError) errors.push(timeError);

  // Role validation
  const roleError = validateEnum(row.role, ASSIGNMENT_ROLES, 'role', rowNumber);
  if (roleError) errors.push(roleError);

  // Future date warning (not an error)
  if (row.date) {
    const date = parseDate(String(row.date));
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (date && date < today) {
      errors.push({
        row: rowNumber,
        column: 'date',
        value: row.date,
        message: 'Assignment date is in the past',
        severity: 'warning',
      });
    }
  }

  return errors;
}

// ============================================================================
// Absence Validation
// ============================================================================

/**
 * Validate an absence import row
 */
export function validateAbsenceRow(
  row: Record<string, unknown>,
  rowNumber: number
): ImportValidationError[] {
  const errors: ImportValidationError[] = [];

  // Required person identifier
  if (!row.person_name && !row.person_id) {
    errors.push({
      row: rowNumber,
      column: 'person_name',
      value: row.person_name,
      message: 'Either person_name or person_id is required',
      severity: 'error',
    });
  }

  // Required fields
  errors.push(...validateRequiredFields(row, ['start_date', 'end_date', 'absence_type'], rowNumber));

  // Date validation
  const startDateError = validateDateFormat(row.start_date, 'start_date', rowNumber);
  if (startDateError) errors.push(startDateError);

  const endDateError = validateDateFormat(row.end_date, 'end_date', rowNumber);
  if (endDateError) errors.push(endDateError);

  // Absence type validation
  const typeError = validateEnum(row.absence_type, ABSENCE_TYPES, 'absence_type', rowNumber);
  if (typeError) errors.push(typeError);

  // Date range validation
  if (row.start_date && row.end_date) {
    const startDate = parseDate(String(row.start_date));
    const endDate = parseDate(String(row.end_date));

    if (startDate && endDate && startDate > endDate) {
      errors.push({
        row: rowNumber,
        column: 'end_date',
        value: row.end_date,
        message: 'End date must be on or after start date',
        severity: 'error',
      });
    }
  }

  // TDY location required for TDY absences
  if (row.absence_type === 'tdy' && !row.tdy_location) {
    errors.push({
      row: rowNumber,
      column: 'tdy_location',
      value: row.tdy_location,
      message: 'TDY location is required for TDY absences',
      severity: 'warning',
    });
  }

  return errors;
}

// ============================================================================
// Schedule Validation
// ============================================================================

/**
 * Validate a schedule import row (bulk assignment)
 */
export function validateScheduleRow(
  row: Record<string, unknown>,
  rowNumber: number
): ImportValidationError[] {
  const errors: ImportValidationError[] = [];

  // Required person identifier
  if (!row.person_name && !row.person_id) {
    errors.push({
      row: rowNumber,
      column: 'person_name',
      value: row.person_name,
      message: 'Either person_name or person_id is required',
      severity: 'error',
    });
  }

  // Required fields
  errors.push(...validateRequiredFields(row, ['date', 'time_of_day', 'role'], rowNumber));

  // Date validation
  const dateError = validateDateFormat(row.date, 'date', rowNumber);
  if (dateError) errors.push(dateError);

  // Time of day validation
  const timeError = validateEnum(row.time_of_day, TIME_OF_DAY, 'time_of_day', rowNumber);
  if (timeError) errors.push(timeError);

  // Role validation
  const roleError = validateEnum(row.role, ASSIGNMENT_ROLES, 'role', rowNumber);
  if (roleError) errors.push(roleError);

  // Rotation or activity required
  if (!row.rotation_name && !row.rotation_template_id && !row.activity_override) {
    errors.push({
      row: rowNumber,
      column: 'rotation_name',
      value: row.rotation_name,
      message: 'Rotation name, rotation template ID, or activity override is required',
      severity: 'warning',
    });
  }

  return errors;
}

// ============================================================================
// Main Validation Function
// ============================================================================

/**
 * Get validation function for data type
 */
function getValidator(
  dataType: ImportDataType
): (row: Record<string, unknown>, rowNumber: number) => ImportValidationError[] {
  const validators: Record<ImportDataType, typeof validatePersonRow> = {
    people: validatePersonRow,
    assignments: validateAssignmentRow,
    absences: validateAbsenceRow,
    schedules: validateScheduleRow,
  };

  return validators[dataType];
}

/**
 * Validate all import data and generate preview
 */
export function validateImportData(
  data: Record<string, unknown>[],
  dataType: ImportDataType,
  columns: string[]
): ImportPreviewResult {
  const validator = getValidator(dataType);
  const rows: ImportPreviewRow[] = [];

  let validRows = 0;
  let errorRows = 0;
  let warningRows = 0;
  let skippedRows = 0;

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    const rowNumber = i + 2; // +2 for 1-indexed and header row

    // Skip empty rows
    if (isEmptyRow(row)) {
      skippedRows++;
      rows.push({
        rowNumber,
        data: row,
        status: 'skipped',
        errors: [],
        warnings: [],
      });
      continue;
    }

    const validationErrors = validator(row, rowNumber);
    const errors = validationErrors.filter(e => e.severity === 'error');
    const warnings = validationErrors.filter(e => e.severity === 'warning');

    let status: ImportPreviewRow['status'];
    if (errors.length > 0) {
      status = 'error';
      errorRows++;
    } else if (warnings.length > 0) {
      status = 'warning';
      warningRows++;
      validRows++; // Warnings are still valid
    } else {
      status = 'valid';
      validRows++;
    }

    rows.push({
      rowNumber,
      data: row,
      status,
      errors,
      warnings,
    });
  }

  return {
    totalRows: data.length,
    validRows,
    errorRows,
    warningRows,
    skippedRows,
    rows,
    columns,
    detectedFormat: 'csv', // Will be set by parser
    dataType,
  };
}

/**
 * Check if a row is empty
 */
function isEmptyRow(row: Record<string, unknown>): boolean {
  return Object.values(row).every(
    value => value === null || value === undefined || value === ''
  );
}

// ============================================================================
// Cross-Row Validation
// ============================================================================

/**
 * Check for duplicate entries
 */
export function findDuplicates(
  data: Record<string, unknown>[],
  dataType: ImportDataType
): ImportValidationError[] {
  const errors: ImportValidationError[] = [];
  const seen = new Map<string, number>();

  // Define unique key generators for each type
  const keyGenerators: Record<ImportDataType, (row: Record<string, unknown>) => string> = {
    people: (row) => String(row.name || '').toLowerCase(),
    assignments: (row) => `${row.date}-${row.time_of_day}-${row.person_name || row.person_id}`,
    absences: (row) => `${row.person_name || row.person_id}-${row.start_date}-${row.end_date}`,
    schedules: (row) => `${row.date}-${row.time_of_day}-${row.person_name || row.person_id}`,
  };

  const generateKey = keyGenerators[dataType];

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    if (isEmptyRow(row)) continue;

    const key = generateKey(row);
    const previousRow = seen.get(key);

    if (previousRow !== undefined) {
      errors.push({
        row: i + 2,
        column: 'duplicate',
        value: key,
        message: `Duplicate entry found (same as row ${previousRow})`,
        severity: 'warning',
      });
    } else {
      seen.set(key, i + 2);
    }
  }

  return errors;
}

/**
 * Validate date ranges don't overlap for absences
 */
export function findOverlappingAbsences(
  data: Record<string, unknown>[]
): ImportValidationError[] {
  const errors: ImportValidationError[] = [];

  // Group by person
  const personAbsences = new Map<string, Array<{ row: number; start: Date; end: Date }>>();

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    if (isEmptyRow(row)) continue;

    const personKey = String(row.person_name || row.person_id);
    const startDate = parseDate(String(row.start_date));
    const endDate = parseDate(String(row.end_date));

    if (!startDate || !endDate) continue;

    if (!personAbsences.has(personKey)) {
      personAbsences.set(personKey, []);
    }

    personAbsences.get(personKey)!.push({
      row: i + 2,
      start: startDate,
      end: endDate,
    });
  }

  // Check for overlaps within each person's absences
  for (const [, absences] of Array.from(personAbsences)) {
    for (let i = 0; i < absences.length; i++) {
      for (let j = i + 1; j < absences.length; j++) {
        const a = absences[i];
        const b = absences[j];

        // Check if date ranges overlap
        if (a.start <= b.end && b.start <= a.end) {
          errors.push({
            row: b.row,
            column: 'date_range',
            value: `${b.start.toISOString().split('T')[0]} to ${b.end.toISOString().split('T')[0]}`,
            message: `Overlapping absence with row ${a.row}`,
            severity: 'warning',
          });
        }
      }
    }
  }

  return errors;
}
