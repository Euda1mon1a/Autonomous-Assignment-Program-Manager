/**
 * CSV Parser Utility
 *
 * Parses CSV files for template import with column mapping and validation.
 */

import type {
  TemplateCreateRequest,
  ActivityType,
} from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export interface CSVParseResult {
  headers: string[];
  rows: Record<string, string>[];
  errors: CSVParseError[];
}

export interface CSVParseError {
  row?: number;
  column?: string;
  message: string;
}

export interface ColumnMapping {
  name: string | null;
  activityType: string | null;
  abbreviation: string | null;
  displayAbbreviation: string | null;
  fontColor: string | null;
  backgroundColor: string | null;
  clinicLocation: string | null;
  maxResidents: string | null;
  requiresSpecialty: string | null;
  requiresProcedureCredential: string | null;
  supervisionRequired: string | null;
  maxSupervisionRatio: string | null;
}

export interface MappedTemplate extends TemplateCreateRequest {
  _rowIndex: number;
  _errors: string[];
}

export interface CSVValidationResult {
  templates: MappedTemplate[];
  validCount: number;
  invalidCount: number;
  errors: CSVParseError[];
}

// ============================================================================
// Constants
// ============================================================================

const VALID_ACTIVITY_TYPES: ActivityType[] = [
  'clinic',
  'inpatient',
  'procedure',
  'procedures',
  'conference',
  'education',
  'outpatient',
  'absence',
  'off',
  'recovery',
];

export const COLUMN_LABELS: Record<keyof ColumnMapping, string> = {
  name: 'Name',
  activityType: 'Activity Type',
  abbreviation: 'Abbreviation',
  displayAbbreviation: 'Display Abbreviation',
  fontColor: 'Font Color',
  backgroundColor: 'Background Color',
  clinicLocation: 'Clinic Location',
  maxResidents: 'Max Residents',
  requiresSpecialty: 'Required Specialty',
  requiresProcedureCredential: 'Requires Procedure Credential',
  supervisionRequired: 'Supervision Required',
  maxSupervisionRatio: 'Max Supervision Ratio',
};

export const REQUIRED_COLUMNS: (keyof ColumnMapping)[] = ['name', 'activityType'];

// ============================================================================
// Helper Functions
// ============================================================================

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
        // Toggle quote state
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }

  result.push(current.trim());
  return result;
}

function normalizeHeader(header: string): string {
  return header
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');
}

function parseBoolean(value: string): boolean {
  const lower = value.toLowerCase().trim();
  return ['true', 'yes', '1', 'y', 'on'].includes(lower);
}

function parseNumber(value: string): number | null {
  if (!value.trim()) return null;
  const num = parseFloat(value);
  return isNaN(num) ? null : num;
}

function parseActivityType(value: string): ActivityType | null {
  const normalized = value.toLowerCase().trim();
  return VALID_ACTIVITY_TYPES.find((t) => t === normalized) || null;
}

function isValidHexColor(color: string): boolean {
  return /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(color);
}

// ============================================================================
// Main Functions
// ============================================================================

/**
 * Parse a CSV string into headers and row objects.
 */
export function parseCSV(csvContent: string): CSVParseResult {
  const errors: CSVParseError[] = [];
  const lines = csvContent.split(/\r?\n/).filter((line) => line.trim());

  if (lines.length === 0) {
    return { headers: [], rows: [], errors: [{ message: 'CSV file is empty' }] };
  }

  // Parse headers
  const headers = parseCSVLine(lines[0]);
  if (headers.length === 0) {
    return {
      headers: [],
      rows: [],
      errors: [{ message: 'No headers found in CSV' }],
    };
  }

  // Parse data rows
  const rows: Record<string, string>[] = [];
  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);

    // Skip empty rows
    if (values.every((v) => !v.trim())) continue;

    const row: Record<string, string> = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || '';
    });
    rows.push(row);
  }

  if (rows.length === 0) {
    errors.push({ message: 'No data rows found in CSV' });
  }

  return { headers, rows, errors };
}

/**
 * Auto-detect column mappings based on header names.
 */
export function autoDetectMapping(headers: string[]): ColumnMapping {
  const mapping: ColumnMapping = {
    name: null,
    activityType: null,
    abbreviation: null,
    displayAbbreviation: null,
    fontColor: null,
    backgroundColor: null,
    clinicLocation: null,
    maxResidents: null,
    requiresSpecialty: null,
    requiresProcedureCredential: null,
    supervisionRequired: null,
    maxSupervisionRatio: null,
  };

  const patterns: Record<keyof ColumnMapping, RegExp[]> = {
    name: [/^name$/i, /template.?name/i, /^template$/i],
    activityType: [/activity.?type/i, /^type$/i, /^activity$/i],
    abbreviation: [/^abbrev/i, /^abbr$/i],
    displayAbbreviation: [/display.?abbrev/i, /short.?name/i],
    fontColor: [/font.?color/i, /text.?color/i, /foreground/i],
    backgroundColor: [/background.?color/i, /bg.?color/i, /^color$/i],
    clinicLocation: [/clinic.?location/i, /location/i, /^clinic$/i],
    maxResidents: [/max.?resident/i, /resident.?limit/i, /capacity/i],
    requiresSpecialty: [/require.?specialty/i, /specialty/i],
    requiresProcedureCredential: [/procedure.?credential/i, /credential/i],
    supervisionRequired: [/supervision/i, /^supervised$/i],
    maxSupervisionRatio: [/supervision.?ratio/i, /ratio/i],
  };

  for (const header of headers) {
    const normalized = normalizeHeader(header);

    for (const [field, fieldPatterns] of Object.entries(patterns)) {
      if (mapping[field as keyof ColumnMapping] === null) {
        for (const pattern of fieldPatterns) {
          if (pattern.test(header) || pattern.test(normalized)) {
            mapping[field as keyof ColumnMapping] = header;
            break;
          }
        }
      }
    }
  }

  return mapping;
}

/**
 * Apply column mapping to parsed rows and validate.
 */
export function applyMappingAndValidate(
  rows: Record<string, string>[],
  mapping: ColumnMapping
): CSVValidationResult {
  const templates: MappedTemplate[] = [];
  const errors: CSVParseError[] = [];
  let validCount = 0;
  let invalidCount = 0;

  // Check required mappings
  for (const required of REQUIRED_COLUMNS) {
    if (!mapping[required]) {
      errors.push({
        message: `Required column "${COLUMN_LABELS[required]}" is not mapped`,
      });
    }
  }

  if (errors.length > 0) {
    return { templates: [], validCount: 0, invalidCount: 0, errors };
  }

  rows.forEach((row, index) => {
    const rowErrors: string[] = [];

    // Get values from mapping
    const name = mapping.name ? row[mapping.name]?.trim() : '';
    const activityTypeRaw = mapping.activityType
      ? row[mapping.activityType]?.trim()
      : '';

    // Validate required fields
    if (!name) {
      rowErrors.push('Name is required');
    }

    const activityType = parseActivityType(activityTypeRaw);
    if (!activityType) {
      rowErrors.push(`Invalid activity type: "${activityTypeRaw}"`);
    }

    // Parse optional fields
    const abbreviation = mapping.abbreviation
      ? row[mapping.abbreviation]?.trim() || null
      : null;

    const displayAbbreviation = mapping.displayAbbreviation
      ? row[mapping.displayAbbreviation]?.trim() || null
      : null;

    const fontColor = mapping.fontColor
      ? row[mapping.fontColor]?.trim() || null
      : null;
    if (fontColor && !isValidHexColor(fontColor)) {
      rowErrors.push(`Invalid font color format: "${fontColor}"`);
    }

    const backgroundColor = mapping.backgroundColor
      ? row[mapping.backgroundColor]?.trim() || null
      : null;
    if (backgroundColor && !isValidHexColor(backgroundColor)) {
      rowErrors.push(`Invalid background color format: "${backgroundColor}"`);
    }

    const clinicLocation = mapping.clinicLocation
      ? row[mapping.clinicLocation]?.trim() || null
      : null;

    const maxResidents = mapping.maxResidents
      ? parseNumber(row[mapping.maxResidents])
      : null;

    const requiresSpecialty = mapping.requiresSpecialty
      ? row[mapping.requiresSpecialty]?.trim() || null
      : null;

    const requiresProcedureCredential = mapping.requiresProcedureCredential
      ? parseBoolean(row[mapping.requiresProcedureCredential])
      : false;

    const supervisionRequired = mapping.supervisionRequired
      ? parseBoolean(row[mapping.supervisionRequired])
      : false;

    const maxSupervisionRatio = mapping.maxSupervisionRatio
      ? parseNumber(row[mapping.maxSupervisionRatio])
      : null;

    const template: MappedTemplate = {
      name,
      activityType: activityType || 'clinic',
      abbreviation,
      displayAbbreviation: displayAbbreviation,
      fontColor: fontColor && isValidHexColor(fontColor) ? fontColor : null,
      backgroundColor:
        backgroundColor && isValidHexColor(backgroundColor) ? backgroundColor : null,
      clinicLocation: clinicLocation,
      maxResidents: maxResidents,
      requiresSpecialty: requiresSpecialty,
      requiresProcedureCredential: requiresProcedureCredential,
      supervisionRequired: supervisionRequired,
      maxSupervisionRatio: maxSupervisionRatio,
      _rowIndex: index + 2, // +2 for 1-based + header
      _errors: rowErrors,
    };

    templates.push(template);

    if (rowErrors.length > 0) {
      invalidCount++;
      rowErrors.forEach((err) => {
        errors.push({ row: index + 2, message: err });
      });
    } else {
      validCount++;
    }
  });

  return { templates, validCount, invalidCount, errors };
}

/**
 * Convert MappedTemplates to TemplateCreateRequest format, filtering invalid ones.
 */
export function toTemplateCreateRequests(
  templates: MappedTemplate[]
): TemplateCreateRequest[] {
  return templates
    .filter((t) => t._errors.length === 0)
    .map(({ _rowIndex: _, _errors: __, ...template }) => template);
}

/**
 * Generate a sample CSV content for download.
 */
export function generateSampleCSV(): string {
  const headers = [
    'name',
    'activityType',
    'abbreviation',
    'displayAbbreviation',
    'maxResidents',
    'supervisionRequired',
    'clinicLocation',
    'backgroundColor',
    'fontColor',
  ];

  const rows = [
    [
      'Cardiology Clinic',
      'clinic',
      'CARD',
      'Cards',
      '4',
      'true',
      'Building A Room 101',
      '#EF4444',
      '#FFFFFF',
    ],
    [
      'General Medicine Inpatient',
      'inpatient',
      'GEN',
      'GenMed',
      '2',
      'false',
      '',
      '#3B82F6',
      '#FFFFFF',
    ],
    [
      'Education Conference',
      'conference',
      'CONF',
      'Conf',
      '',
      'false',
      '',
      '#EAB308',
      '#000000',
    ],
  ];

  const lines = [
    headers.join(','),
    ...rows.map((row) =>
      row.map((cell) => (cell.includes(',') ? `"${cell}"` : cell)).join(',')
    ),
  ];

  return lines.join('\n');
}
