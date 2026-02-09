import {
  parseCSV,
  autoDetectMapping,
  applyMappingAndValidate,
  generateSampleCSV,
  COLUMN_LABELS,
  REQUIRED_COLUMNS,
} from '../csvParser';
import type { ColumnMapping } from '../csvParser';

describe('parseCSV', () => {
  it('parses simple CSV', () => {
    const csv = 'name,type\nFoo,clinic\nBar,inpatient';
    const result = parseCSV(csv);
    expect(result.headers).toEqual(['name', 'type']);
    expect(result.rows).toHaveLength(2);
    expect(result.rows[0]['name']).toBe('Foo');
    expect(result.rows[1]['type']).toBe('inpatient');
    expect(result.errors).toHaveLength(0);
  });

  it('handles quoted fields with commas', () => {
    const csv = 'name,location\n"Smith, John","Building A, Room 1"';
    const result = parseCSV(csv);
    expect(result.rows[0]['name']).toBe('Smith, John');
    expect(result.rows[0]['location']).toBe('Building A, Room 1');
  });

  it('handles escaped quotes', () => {
    const csv = 'name\n"""quoted"""';
    const result = parseCSV(csv);
    expect(result.rows[0]['name']).toBe('"quoted"');
  });

  it('returns error for empty CSV', () => {
    const result = parseCSV('');
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0].message).toContain('empty');
  });

  it('returns error for headers only', () => {
    const result = parseCSV('name,type');
    expect(result.rows).toHaveLength(0);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0].message).toContain('No data rows');
  });

  it('skips empty rows', () => {
    const csv = 'name\nFoo\n\nBar';
    const result = parseCSV(csv);
    expect(result.rows).toHaveLength(2);
  });

  it('handles Windows line endings', () => {
    const csv = 'name\r\nFoo\r\nBar';
    const result = parseCSV(csv);
    expect(result.rows).toHaveLength(2);
  });

  it('trims field values', () => {
    const csv = 'name\n  Foo  ';
    const result = parseCSV(csv);
    expect(result.rows[0]['name']).toBe('Foo');
  });
});

describe('autoDetectMapping', () => {
  it('detects standard column names', () => {
    const headers = ['name', 'activityType', 'abbreviation'];
    const mapping = autoDetectMapping(headers);
    expect(mapping.name).toBe('name');
    expect(mapping.activityType).toBe('activityType');
    expect(mapping.abbreviation).toBe('abbreviation');
  });

  it('detects alternative column names', () => {
    const headers = ['Template Name', 'Activity Type', 'Abbrev'];
    const mapping = autoDetectMapping(headers);
    expect(mapping.name).toBeTruthy();
    expect(mapping.activityType).toBeTruthy();
    expect(mapping.abbreviation).toBeTruthy();
  });

  it('detects color columns', () => {
    const headers = ['Font Color', 'Background Color'];
    const mapping = autoDetectMapping(headers);
    expect(mapping.fontColor).toBeTruthy();
    expect(mapping.backgroundColor).toBeTruthy();
  });

  it('returns null for unrecognized columns', () => {
    const headers = ['random_field', 'other_data'];
    const mapping = autoDetectMapping(headers);
    expect(mapping.name).toBeNull();
    expect(mapping.activityType).toBeNull();
  });

  it('detects supervision columns', () => {
    const headers = ['supervision', 'ratio'];
    const mapping = autoDetectMapping(headers);
    expect(mapping.supervisionRequired).toBeTruthy();
    expect(mapping.maxSupervisionRatio).toBeTruthy();
  });
});

describe('applyMappingAndValidate', () => {
  const validMapping: ColumnMapping = {
    name: 'name',
    activityType: 'type',
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

  it('validates valid rows', () => {
    const rows = [{ name: 'Test', type: 'clinic' }];
    const result = applyMappingAndValidate(rows, validMapping);
    expect(result.validCount).toBe(1);
    expect(result.invalidCount).toBe(0);
  });

  it('rejects missing name', () => {
    const rows = [{ name: '', type: 'clinic' }];
    const result = applyMappingAndValidate(rows, validMapping);
    expect(result.invalidCount).toBe(1);
    expect(result.errors.some((e) => e.message.includes('Name is required'))).toBe(true);
  });

  it('rejects invalid activity type', () => {
    const rows = [{ name: 'Test', type: 'invalid_type' }];
    const result = applyMappingAndValidate(rows, validMapping);
    expect(result.invalidCount).toBe(1);
    expect(result.errors.some((e) => e.message.includes('Invalid activity type'))).toBe(true);
  });

  it('rejects missing required column mapping', () => {
    const badMapping = { ...validMapping, name: null };
    const result = applyMappingAndValidate([], badMapping);
    expect(result.errors.length).toBeGreaterThan(0);
    expect(result.errors[0].message).toContain('not mapped');
  });

  it('validates hex colors', () => {
    const mapping = { ...validMapping, fontColor: 'color' };
    const rows = [{ name: 'Test', type: 'clinic', color: 'not-a-color' }];
    const result = applyMappingAndValidate(rows, mapping);
    expect(result.errors.some((e) => e.message.includes('Invalid font color'))).toBe(true);
  });

  it('accepts valid hex colors', () => {
    const mapping = { ...validMapping, fontColor: 'color' };
    const rows = [{ name: 'Test', type: 'clinic', color: '#FF0000' }];
    const result = applyMappingAndValidate(rows, mapping);
    expect(result.validCount).toBe(1);
    expect(result.templates[0].fontColor).toBe('#FF0000');
  });

  it('parses boolean fields', () => {
    const mapping = { ...validMapping, supervisionRequired: 'supervised' };
    const rows = [{ name: 'Test', type: 'clinic', supervised: 'yes' }];
    const result = applyMappingAndValidate(rows, mapping);
    expect(result.templates[0].supervisionRequired).toBe(true);
  });

  it('parses numeric fields', () => {
    const mapping = { ...validMapping, maxResidents: 'max' };
    const rows = [{ name: 'Test', type: 'clinic', max: '4' }];
    const result = applyMappingAndValidate(rows, mapping);
    expect(result.templates[0].maxResidents).toBe(4);
  });

  it('sets row index correctly', () => {
    const rows = [{ name: 'First', type: 'clinic' }, { name: 'Second', type: 'inpatient' }];
    const result = applyMappingAndValidate(rows, validMapping);
    // Row index is 1-based + header offset
    expect(result.templates[0]._rowIndex).toBe(2);
    expect(result.templates[1]._rowIndex).toBe(3);
  });
});

describe('generateSampleCSV', () => {
  it('produces valid CSV with headers and rows', () => {
    const csv = generateSampleCSV();
    const result = parseCSV(csv);
    expect(result.headers.length).toBeGreaterThan(0);
    expect(result.rows.length).toBeGreaterThan(0);
    expect(result.errors).toHaveLength(0);
  });

  it('includes required columns', () => {
    const csv = generateSampleCSV();
    const result = parseCSV(csv);
    expect(result.headers).toContain('name');
    expect(result.headers).toContain('activityType');
  });
});

describe('constants', () => {
  it('has labels for all column mapping fields', () => {
    const mappingKeys: (keyof ColumnMapping)[] = [
      'name', 'activityType', 'abbreviation', 'displayAbbreviation',
      'fontColor', 'backgroundColor', 'clinicLocation', 'maxResidents',
      'requiresSpecialty', 'requiresProcedureCredential',
      'supervisionRequired', 'maxSupervisionRatio',
    ];
    for (const key of mappingKeys) {
      expect(COLUMN_LABELS[key]).toBeTruthy();
    }
  });

  it('requires name and activityType columns', () => {
    expect(REQUIRED_COLUMNS).toContain('name');
    expect(REQUIRED_COLUMNS).toContain('activityType');
  });
});
