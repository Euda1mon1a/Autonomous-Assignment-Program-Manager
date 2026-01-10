/**
 * Utility functions for parsing and processing import/export data
 */

import type {
  ImportFileFormat,
  ImportDataType,
  ImportValidationError,
  ExportFormat,
  ExportColumn,
} from './types';

// ============================================================================
// File Detection & Parsing
// ============================================================================

/**
 * Detect file format from file extension or MIME type
 */
export function detectFileFormat(file: File): ImportFileFormat {
  const extension = file.name.split('.').pop()?.toLowerCase();

  if (extension === 'csv' || file.type === 'text/csv') {
    return 'csv';
  }

  if (extension === 'xlsx' || extension === 'xls' ||
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.type === 'application/vnd.ms-excel') {
    return 'xlsx';
  }

  if (extension === 'json' || file.type === 'application/json') {
    return 'json';
  }

  // Default to CSV
  return 'csv';
}

/**
 * Parse CSV content into array of objects
 */
export function parseCSV(content: string): Record<string, unknown>[] {
  const lines = content.split(/\r?\n/).filter(line => line.trim());

  if (lines.length === 0) {
    return [];
  }

  // Parse header row
  const headers = parseCSVLine(lines[0]);

  // Parse data rows
  const data: Record<string, unknown>[] = [];

  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);
    const row: Record<string, unknown> = {};

    headers.forEach((header, index) => {
      const value = values[index];
      row[header.trim()] = parseValue(value);
    });

    data.push(row);
  }

  return data;
}

/**
 * Parse a single CSV line handling quoted values
 */
function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    const nextChar = line[i + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        // Escaped quote
        current += '"';
        i++;
      } else {
        // Toggle quote mode
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += char;
    }
  }

  // Add last field
  result.push(current);

  return result;
}

/**
 * Parse a string value into appropriate type
 */
export function parseValue(value: string | undefined | null): string | number | boolean | null {
  if (value === undefined || value === null || value === '') {
    return null;
  }

  const trimmed = value.trim();

  // Boolean values
  if (trimmed.toLowerCase() === 'true' || trimmed.toLowerCase() === 'yes') {
    return true;
  }
  if (trimmed.toLowerCase() === 'false' || trimmed.toLowerCase() === 'no') {
    return false;
  }

  // Numeric values
  if (/^-?\d+$/.test(trimmed)) {
    return parseInt(trimmed, 10);
  }
  if (/^-?\d+\.\d+$/.test(trimmed)) {
    return parseFloat(trimmed);
  }

  return trimmed;
}

/**
 * Parse JSON content
 */
export function parseJSON(content: string): Record<string, unknown>[] {
  const parsed = JSON.parse(content);

  if (Array.isArray(parsed)) {
    return parsed;
  }

  // Handle single object
  if (typeof parsed === 'object' && parsed !== null) {
    return [parsed];
  }

  throw new Error('Invalid JSON format: expected array or object');
}

/**
 * Read file content as text
 */
export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}

/**
 * Read file content as ArrayBuffer (for Excel files)
 */
export function readFileAsArrayBuffer(file: File): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsArrayBuffer(file);
  });
}

// ============================================================================
// Data Type Detection
// ============================================================================

/**

/**
 * Detect import data type from column headers
 *
 * IMPORTANT: Check order matters! 'people' must be checked before 'schedules'
 * because the loose matching in hasRequiredColumns causes 'personname'.includes('name')
 * to incorrectly match a 'name' column.
 */
export function detectDataType(columns: string[]): ImportDataType {
  const normalizedColumns = columns.map(c => c.toLowerCase().replace(/[_\s-]/g, ''));

  // Check for people columns FIRST (before schedules)
  // This prevents 'name' from matching 'personname' via loose includes()
  if (hasRequiredColumns(normalizedColumns, ['name', 'type']) &&
      !normalizedColumns.some(c => c === 'date' || c === 'timeofday')) {
    return 'people';
  }

  // Check for absence columns
  if (hasRequiredColumns(normalizedColumns, ['startdate', 'enddate', 'absencetype'])) {
    return 'absences';
  }

  // Check for schedule-specific columns
  if (hasRequiredColumns(normalizedColumns, ['date', 'timeofday', 'personname', 'role'])) {
    return 'schedules';
  }

  // Check for assignment columns
  if (hasRequiredColumns(normalizedColumns, ['date', 'timeofday', 'role'])) {
    return 'assignments';
  }

  // Default to people (safer default - user can change if wrong)
  return 'people';
}

/**
 * Check if columns contain required fields
 */
function hasRequiredColumns(columns: string[], required: string[]): boolean {
  return required.every(req =>
    columns.some(col => col.includes(req) || req.includes(col))
  );
}

// ============================================================================
// Column Normalization
// ============================================================================

/**
 * Column name aliases for mapping
 */
const COLUMN_ALIASES: Record<string, string[]> = {
  name: ['name', 'full_name', 'fullname', 'personName', 'personname'],
  email: ['email', 'emailAddress', 'emailaddress', 'mail'],
  type: ['type', 'person_type', 'persontype', 'roleType'],
  pgyLevel: ['pgyLevel', 'pgylevel', 'pgy', 'year', 'training_year'],
  performsProcedures: ['performsProcedures', 'performsprocedures', 'procedures', 'can_do_procedures'],
  specialties: ['specialties', 'specialty', 'specialization'],
  primaryDuty: ['primaryDuty', 'primaryduty', 'duty', 'main_duty'],
  date: ['date', 'assignment_date', 'block_date', 'scheduleDate'],
  timeOfDay: ['timeOfDay', 'timeofday', 'time', 'period', 'am_pm', 'ampm'],
  personName: ['personName', 'personname', 'residentName', 'facultyName', 'name'],
  personId: ['personId', 'personid', 'residentId', 'facultyId'],
  rotationName: ['rotationName', 'rotationname', 'rotation', 'activity'],
  rotationTemplateId: ['rotationTemplateId', 'rotationtemplateid', 'templateId'],
  role: ['role', 'assignment_role', 'position'],
  activityOverride: ['activityOverride', 'activityoverride', 'override', 'custom_activity'],
  notes: ['notes', 'note', 'comments', 'comment', 'description'],
  startDate: ['startDate', 'startdate', 'from_date', 'from', 'begin_date'],
  endDate: ['endDate', 'enddate', 'to_date', 'to', 'finish_date'],
  absenceType: ['absenceType', 'absencetype', 'leave_type', 'type'],
  deploymentOrders: ['deploymentOrders', 'deploymentorders', 'orders', 'military_orders'],
  tdyLocation: ['tdyLocation', 'tdylocation', 'location', 'duty_location'],
  replacementActivity: ['replacementActivity', 'replacementactivity', 'replacement', 'alternate'],
};

/**
 * Normalize column name to standard field name
 */
export function normalizeColumnName(column: string): string {
  const normalized = column.toLowerCase().replace(/[_\s-]/g, '');

  for (const [standard, aliases] of Object.entries(COLUMN_ALIASES)) {
    if (aliases.some(alias => alias.replace(/[_\s-]/g, '') === normalized)) {
      return standard;
    }
  }

  return column;
}

/**
 * Map raw data columns to normalized column names
 */
export function normalizeColumns(data: Record<string, unknown>[]): Record<string, unknown>[] {
  return data.map(row => {
    const normalized: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(row)) {
      const normalizedKey = normalizeColumnName(key);
      normalized[normalizedKey] = value;
    }

    return normalized;
  });
}

// ============================================================================
// Export Utilities
// ============================================================================

/**
 * Format value for export
 */
export function formatExportValue(value: unknown, format?: (v: unknown) => string): string {
  if (format) {
    return format(value);
  }

  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }

  if (Array.isArray(value)) {
    return value.join(', ');
  }

  if (value instanceof Date) {
    return value.toISOString().split('T')[0];
  }

  return String(value);
}

/**
 * Generate CSV content from data
 */
export function generateCSV(
  data: Record<string, unknown>[],
  columns: ExportColumn[],
  includeHeaders = true
): string {
  const lines: string[] = [];

  // Add header row
  if (includeHeaders) {
    const headerRow = columns.map(col => escapeCSVValue(col.header)).join(',');
    lines.push(headerRow);
  }

  // Add data rows
  for (const row of data) {
    const values = columns.map(col => {
      const value = getNestedValue(row, col.key);
      const formatted = formatExportValue(value, col.format);
      return escapeCSVValue(formatted);
    });
    lines.push(values.join(','));
  }

  return lines.join('\n');
}

/**
 * Escape a value for CSV format
 */
function escapeCSVValue(value: string): string {
  if (value.includes(',') || value.includes('\n') || value.includes('"')) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

/**
 * Get nested value from object using dot notation
 */
export function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, key) => {
    if (acc && typeof acc === 'object' && key in acc) {
      return (acc as Record<string, unknown>)[key];
    }
    return undefined;
  }, obj);
}

/**
 * Generate JSON content from data
 */
export function generateJSON(data: Record<string, unknown>[], pretty = true): string {
  return JSON.stringify(data, null, pretty ? 2 : undefined);
}

/**
 * Download file in browser
 */
export function downloadFile(content: string | Blob, filename: string, mimeType: string): void {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Get MIME type for export format
 */
export function getMimeType(format: ExportFormat): string {
  const mimeTypes: Record<ExportFormat, string> = {
    csv: 'text/csv;charset=utf-8;',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    pdf: 'application/pdf',
    json: 'application/json',
  };
  return mimeTypes[format];
}

/**
 * Get file extension for export format
 */
export function getFileExtension(format: ExportFormat): string {
  return `.${format}`;
}

// ============================================================================
// Date Utilities
// ============================================================================

/**
 * Parse date string in various formats
 */
export function parseDate(value: string, _format = 'YYYY-MM-DD'): Date | null {
  if (!value) return null;

  // Try ISO format first
  const isoDate = new Date(value);
  if (!isNaN(isoDate.getTime())) {
    return isoDate;
  }

  // Try common formats
  const formats = [
    /^(\d{4})-(\d{2})-(\d{2})$/, // YYYY-MM-DD
    /^(\d{2})\/(\d{2})\/(\d{4})$/, // MM/DD/YYYY
    /^(\d{2})-(\d{2})-(\d{4})$/, // MM-DD-YYYY
    /^(\d{2})\.(\d{2})\.(\d{4})$/, // DD.MM.YYYY
  ];

  for (const regex of formats) {
    const match = value.match(regex);
    if (match) {
      // Determine date parts based on format
      let year: number, month: number, day: number;

      if (regex.source.startsWith('^(\\d{4})')) {
        [, year, month, day] = match.map(Number);
      } else if (regex.source.includes('/')) {
        [, month, day, year] = match.map(Number);
      } else {
        [, day, month, year] = match.map(Number);
      }

      const date = new Date(year, month - 1, day);
      if (!isNaN(date.getTime())) {
        return date;
      }
    }
  }

  return null;
}

/**
 * Format date to string
 */
export function formatDate(date: Date, format = 'YYYY-MM-DD'): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day);
}

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Validate required fields are present
 */
export function validateRequiredFields(
  row: Record<string, unknown>,
  requiredFields: string[],
  rowNumber: number
): ImportValidationError[] {
  const errors: ImportValidationError[] = [];

  for (const field of requiredFields) {
    const value = row[field];
    if (value === null || value === undefined || value === '') {
      errors.push({
        row: rowNumber,
        column: field,
        value,
        message: `${field} is required`,
        severity: 'error',
      });
    }
  }

  return errors;
}

/**
 * Validate field value is in allowed values
 */
export function validateEnum(
  value: unknown,
  allowedValues: string[],
  field: string,
  rowNumber: number
): ImportValidationError | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const stringValue = String(value).toLowerCase();
  const normalizedAllowed = allowedValues.map(v => v.toLowerCase());

  if (!normalizedAllowed.includes(stringValue)) {
    return {
      row: rowNumber,
      column: field,
      value,
      message: `Invalid ${field}: must be one of ${allowedValues.join(', ')}`,
      severity: 'error',
    };
  }

  return null;
}

/**
 * Validate email format
 */
export function validateEmail(
  value: unknown,
  field: string,
  rowNumber: number
): ImportValidationError | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(String(value))) {
    return {
      row: rowNumber,
      column: field,
      value,
      message: 'Invalid email format',
      severity: 'error',
    };
  }

  return null;
}

/**
 * Validate date format
 */
export function validateDateFormat(
  value: unknown,
  field: string,
  rowNumber: number
): ImportValidationError | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const date = parseDate(String(value));
  if (!date) {
    return {
      row: rowNumber,
      column: field,
      value,
      message: 'Invalid date format. Expected YYYY-MM-DD',
      severity: 'error',
    };
  }

  return null;
}

/**
 * Validate numeric range
 */
export function validateNumericRange(
  value: unknown,
  field: string,
  min: number,
  max: number,
  rowNumber: number
): ImportValidationError | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const num = Number(value);
  if (isNaN(num)) {
    return {
      row: rowNumber,
      column: field,
      value,
      message: `${field} must be a number`,
      severity: 'error',
    };
  }

  if (num < min || num > max) {
    return {
      row: rowNumber,
      column: field,
      value,
      message: `${field} must be between ${min} and ${max}`,
      severity: 'error',
    };
  }

  return null;
}
