/**
 * Mock data factories for import-export tests
 * Provides reusable mock data for import-export feature tests
 */

import type {
  ExportFormat,
  ExportColumn,
  ExportOptions,
  ExportProgress,
  ImportDataType,
  ImportFileFormat,
  ImportValidationError,
  ImportRowStatus,
  ImportPreviewRow,
  ImportPreviewResult,
  ImportProgress,
  ImportOptions,
  ImportResult,
} from '@/features/import-export/types';

/**
 * Mock data factories
 */
export const importExportMockFactories = {
  exportColumn: (overrides: Partial<ExportColumn> = {}): ExportColumn => ({
    key: 'name',
    header: 'Name',
    width: 150,
    format: (value) => String(value),
    ...overrides,
  }),

  exportOptions: (overrides: Partial<ExportOptions> = {}): ExportOptions => ({
    format: 'csv' as ExportFormat,
    filename: 'export-data',
    columns: [
      importExportMockFactories.exportColumn({ key: 'name', header: 'Name' }),
      importExportMockFactories.exportColumn({ key: 'email', header: 'Email' }),
    ],
    includeHeaders: true,
    dateFormat: 'YYYY-MM-DD',
    title: 'Data Export',
    subtitle: 'Exported on 2024-02-15',
    ...overrides,
  }),

  exportProgress: (overrides: Partial<ExportProgress> = {}): ExportProgress => ({
    status: 'idle',
    currentRow: 0,
    totalRows: 0,
    message: 'Ready to export',
    ...overrides,
  }),

  importValidationError: (
    overrides: Partial<ImportValidationError> = {}
  ): ImportValidationError => ({
    row: 1,
    column: 'email',
    value: 'invalid-email',
    message: 'Invalid email format',
    severity: 'error',
    ...overrides,
  }),

  importPreviewRow: <T = Record<string, unknown>>(
    overrides: Partial<ImportPreviewRow<T>> = {}
  ): ImportPreviewRow<T> => ({
    rowNumber: 1,
    data: { name: 'Dr. John Smith', email: 'john.smith@hospital.org' } as T,
    status: 'valid' as ImportRowStatus,
    errors: [],
    warnings: [],
    ...overrides,
  }),

  importPreviewResult: <T = Record<string, unknown>>(
    overrides: Partial<ImportPreviewResult<T>> = {}
  ): ImportPreviewResult<T> => ({
    totalRows: 10,
    validRows: 8,
    errorRows: 1,
    warningRows: 1,
    skippedRows: 0,
    rows: [
      importExportMockFactories.importPreviewRow<T>(),
      importExportMockFactories.importPreviewRow<T>({
        rowNumber: 2,
        status: 'error',
        errors: [importExportMockFactories.importValidationError({ row: 2 })],
      }),
    ],
    columns: ['name', 'email', 'type'],
    detectedFormat: 'csv' as ImportFileFormat,
    dataType: 'people' as ImportDataType,
    ...overrides,
  }),

  importProgress: (overrides: Partial<ImportProgress> = {}): ImportProgress => ({
    status: 'idle',
    currentRow: 0,
    totalRows: 0,
    processedRows: 0,
    successCount: 0,
    errorCount: 0,
    warningCount: 0,
    message: 'Ready to import',
    errors: [],
    ...overrides,
  }),

  importOptions: (overrides: Partial<ImportOptions> = {}): ImportOptions => ({
    skipDuplicates: true,
    updateExisting: false,
    skipInvalidRows: false,
    dateFormat: 'YYYY-MM-DD',
    trimWhitespace: true,
    ...overrides,
  }),

  importResult: (overrides: Partial<ImportResult> = {}): ImportResult => ({
    success: true,
    totalProcessed: 10,
    successCount: 9,
    errorCount: 1,
    skippedCount: 0,
    errors: [],
    importedIds: ['id-1', 'id-2', 'id-3'],
    ...overrides,
  }),
};

/**
 * Mock API responses
 */
export const importExportMockResponses = {
  exportData: [
    { id: '1', name: 'Dr. John Smith', email: 'john.smith@hospital.org', type: 'resident' },
    { id: '2', name: 'Dr. Jane Doe', email: 'jane.doe@hospital.org', type: 'faculty' },
    { id: '3', name: 'Dr. Bob Johnson', email: 'bob.johnson@hospital.org', type: 'resident' },
  ],

  exportColumns: [
    importExportMockFactories.exportColumn({ key: 'name', header: 'Name' }),
    importExportMockFactories.exportColumn({ key: 'email', header: 'Email' }),
    importExportMockFactories.exportColumn({ key: 'type', header: 'Type' }),
  ],

  exportBlob: new Blob(['test data'], { type: 'text/csv' }),

  importPreview: importExportMockFactories.importPreviewResult(),

  importResult: importExportMockFactories.importResult(),
};
