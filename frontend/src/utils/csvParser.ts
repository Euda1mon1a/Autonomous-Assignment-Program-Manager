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
  activity_type: string | null;
  abbreviation: string | null;
  display_abbreviation: string | null;
  font_color: string | null;
  background_color: string | null;
  clinic_location: string | null;
  max_residents: string | null;
  requires_specialty: string | null;
  requires_procedure_credential: string | null;
  supervision_required: string | null;
  max_supervision_ratio: string | null;
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
  activity_type: 'Activity Type',
  abbreviation: 'Abbreviation',
  display_abbreviation: 'Display Abbreviation',
  font_color: 'Font Color',
  background_color: 'Background Color',
  clinic_location: 'Clinic Location',
  max_residents: 'Max Residents',
  requires_specialty: 'Required Specialty',
  requires_procedure_credential: 'Requires Procedure Credential',
  supervision_required: 'Supervision Required',
  max_supervision_ratio: 'Max Supervision Ratio',
};

export const REQUIRED_COLUMNS: (keyof ColumnMapping)[] = ['name', 'activity_type'];

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
    activity_type: null,
    abbreviation: null,
    display_abbreviation: null,
    font_color: null,
    background_color: null,
    clinic_location: null,
    max_residents: null,
    requires_specialty: null,
    requires_procedure_credential: null,
    supervision_required: null,
    max_supervision_ratio: null,
  };

  const patterns: Record<keyof ColumnMapping, RegExp[]> = {
    name: [/^name$/i, /template.?name/i, /^template$/i],
    activity_type: [/activity.?type/i, /^type$/i, /^activity$/i],
    abbreviation: [/^abbrev/i, /^abbr$/i],
    display_abbreviation: [/display.?abbrev/i, /short.?name/i],
    font_color: [/font.?color/i, /text.?color/i, /foreground/i],
    background_color: [/background.?color/i, /bg.?color/i, /^color$/i],
    clinic_location: [/clinic.?location/i, /location/i, /^clinic$/i],
    max_residents: [/max.?resident/i, /resident.?limit/i, /capacity/i],
    requires_specialty: [/require.?specialty/i, /specialty/i],
    requires_procedure_credential: [/procedure.?credential/i, /credential/i],
    supervision_required: [/supervision/i, /^supervised$/i],
    max_supervision_ratio: [/supervision.?ratio/i, /ratio/i],
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
    const activityTypeRaw = mapping.activity_type
      ? row[mapping.activity_type]?.trim()
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

    const displayAbbreviation = mapping.display_abbreviation
      ? row[mapping.display_abbreviation]?.trim() || null
      : null;

    const fontColor = mapping.font_color
      ? row[mapping.font_color]?.trim() || null
      : null;
    if (fontColor && !isValidHexColor(fontColor)) {
      rowErrors.push(`Invalid font color format: "${fontColor}"`);
    }

    const backgroundColor = mapping.background_color
      ? row[mapping.background_color]?.trim() || null
      : null;
    if (backgroundColor && !isValidHexColor(backgroundColor)) {
      rowErrors.push(`Invalid background color format: "${backgroundColor}"`);
    }

    const clinicLocation = mapping.clinic_location
      ? row[mapping.clinic_location]?.trim() || null
      : null;

    const maxResidents = mapping.max_residents
      ? parseNumber(row[mapping.max_residents])
      : null;

    const requiresSpecialty = mapping.requires_specialty
      ? row[mapping.requires_specialty]?.trim() || null
      : null;

    const requiresProcedureCredential = mapping.requires_procedure_credential
      ? parseBoolean(row[mapping.requires_procedure_credential])
      : false;

    const supervisionRequired = mapping.supervision_required
      ? parseBoolean(row[mapping.supervision_required])
      : false;

    const maxSupervisionRatio = mapping.max_supervision_ratio
      ? parseNumber(row[mapping.max_supervision_ratio])
      : null;

    const template: MappedTemplate = {
      name,
      activity_type: activityType || 'clinic',
      abbreviation,
      display_abbreviation: displayAbbreviation,
      font_color: fontColor && isValidHexColor(fontColor) ? fontColor : null,
      background_color:
        backgroundColor && isValidHexColor(backgroundColor) ? backgroundColor : null,
      clinic_location: clinicLocation,
      max_residents: maxResidents,
      requires_specialty: requiresSpecialty,
      requires_procedure_credential: requiresProcedureCredential,
      supervision_required: supervisionRequired,
      max_supervision_ratio: maxSupervisionRatio,
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
    'activity_type',
    'abbreviation',
    'display_abbreviation',
    'max_residents',
    'supervision_required',
    'clinic_location',
    'background_color',
    'font_color',
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
