/**
 * Bulk Import/Export Feature
 *
 * This module provides comprehensive import/export functionality for the
 * Residency Scheduler application, including:
 *
 * - CSV/Excel/JSON file import with validation
 * - Export to CSV, Excel, JSON, and PDF formats
 * - Progress tracking for large imports
 * - Data preview and confirmation before import
 * - Error handling and validation feedback
 *
 * @example
 * ```tsx
 * import {
 *   BulkImportModal,
 *   ExportPanel,
 *   useImport,
 *   useExport,
 * } from '@/features/import-export';
 *
 * // Use the import modal
 * <BulkImportModal
 *   isOpen={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   defaultDataType="schedules"
 * />
 *
 * // Use the export panel
 * <ExportPanel
 *   data={scheduleData}
 *   columns={scheduleColumns}
 *   filename="schedule-export"
 * />
 * ```
 */

// ============================================================================
// Types
// ============================================================================

export type {
  // Import types
  ImportDataType,
  ImportFileFormat,
  ImportValidationError,
  ImportRowStatus,
  ImportPreviewRow,
  ImportPreviewResult,
  ImportProgress,
  ImportOptions,
  ImportResult,
  // Export types
  ExportFormat,
  ExportColumn,
  ExportOptions,
  ExportProgress,
  // Data row types
  PersonImportRow,
  AssignmentImportRow,
  AbsenceImportRow,
  ScheduleImportRow,
  ImportDataMap,
  ExportDataMap,
  FileDropState,
} from './types';

// ============================================================================
// Hooks
// ============================================================================

export { useImport, type UseImportReturn } from './useImport';
export {
  useExport,
  type UseExportReturn,
  PEOPLE_EXPORT_COLUMNS,
  ASSIGNMENT_EXPORT_COLUMNS,
  ABSENCE_EXPORT_COLUMNS,
  SCHEDULE_EXPORT_COLUMNS,
} from './useExport';

// ============================================================================
// Components
// ============================================================================

export { BulkImportModal } from './BulkImportModal';
export { ImportPreview, ImportPreviewSkeleton } from './ImportPreview';
export {
  ImportProgressIndicator,
  ImportProgressSkeleton,
} from './ImportProgressIndicator';
export {
  ExportPanel,
  QuickExportButton,
  ExportModal,
} from './ExportPanel';

// ============================================================================
// Utilities
// ============================================================================

export {
  // File detection & parsing
  detectFileFormat,
  parseCSV,
  parseJSON,
  readFileAsText,
  readFileAsArrayBuffer,
  // Data type detection
  detectDataType,
  // Column normalization
  normalizeColumnName,
  normalizeColumns,
  // Export utilities
  formatExportValue,
  generateCSV,
  generateJSON,
  downloadFile,
  getMimeType,
  getFileExtension,
  // Date utilities
  parseDate,
  formatDate,
  // Validation helpers
  validateRequiredFields,
  validateEnum,
  validateEmail,
  validateDateFormat,
  validateNumericRange,
  getNestedValue,
  parseValue,
} from './utils';

export {
  // Validation functions
  validatePersonRow,
  validateAssignmentRow,
  validateAbsenceRow,
  validateScheduleRow,
  validateImportData,
  // Cross-row validation
  findDuplicates,
  findOverlappingAbsences,
} from './validation';
