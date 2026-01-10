/**
 * React hook for handling bulk exports to multiple formats
 */

import { useState, useCallback } from 'react';
import type {
  ExportColumn,
  ExportOptions,
  ExportProgress,
} from './types';
import {
  generateCSV,
  generateJSON,
  downloadFile,
  getMimeType,
  getFileExtension,
  formatExportValue,
} from './utils';

// ============================================================================
// Default Column Configurations
// ============================================================================

export const PEOPLE_EXPORT_COLUMNS: ExportColumn[] = [
  { key: 'name', header: 'Name' },
  { key: 'email', header: 'Email' },
  { key: 'type', header: 'Type' },
  { key: 'pgyLevel', header: 'PGY Level' },
  { key: 'performsProcedures', header: 'Performs Procedures', format: (v) => v ? 'Yes' : 'No' },
  { key: 'specialties', header: 'Specialties', format: (v) => Array.isArray(v) ? v.join(', ') : String(v || '') },
  { key: 'primaryDuty', header: 'Primary Duty' },
];

export const ASSIGNMENT_EXPORT_COLUMNS: ExportColumn[] = [
  { key: 'blockId', header: 'Block ID' },
  { key: 'personId', header: 'Person ID' },
  { key: 'role', header: 'Role' },
  { key: 'rotationTemplateId', header: 'Rotation Template ID' },
  { key: 'activityOverride', header: 'Activity Override' },
  { key: 'notes', header: 'Notes' },
  { key: 'createdAt', header: 'Created At' },
];

export const ABSENCE_EXPORT_COLUMNS: ExportColumn[] = [
  { key: 'personId', header: 'Person ID' },
  { key: 'startDate', header: 'Start Date' },
  { key: 'endDate', header: 'End Date' },
  { key: 'absenceType', header: 'Absence Type' },
  { key: 'deploymentOrders', header: 'Deployment Orders', format: (v) => v ? 'Yes' : 'No' },
  { key: 'tdyLocation', header: 'TDY Location' },
  { key: 'replacementActivity', header: 'Replacement Activity' },
  { key: 'notes', header: 'Notes' },
];

export const SCHEDULE_EXPORT_COLUMNS: ExportColumn[] = [
  { key: 'date', header: 'Date' },
  { key: 'timeOfDay', header: 'Time of Day' },
  { key: 'personName', header: 'Person Name' },
  { key: 'person_type', header: 'Person Type' },
  { key: 'role', header: 'Role' },
  { key: 'activity', header: 'Activity' },
  { key: 'abbreviation', header: 'Abbreviation' },
];

// ============================================================================
// Types
// ============================================================================

interface UseExportOptions {
  onProgress?: (progress: ExportProgress) => void;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useExport(hookOptions: UseExportOptions = {}) {
  const [progress, setProgress] = useState<ExportProgress>({
    status: 'idle',
    currentRow: 0,
    totalRows: 0,
    message: '',
  });

  // ============================================================================
  // Update Progress
  // ============================================================================

  const updateProgress = useCallback((updates: Partial<ExportProgress>) => {
    setProgress(prev => {
      const newProgress = { ...prev, ...updates };
      hookOptions.onProgress?.(newProgress);
      return newProgress;
    });
  }, [hookOptions]);

  // ============================================================================
  // Export to CSV
  // ============================================================================

  const exportToCSV = useCallback(async (
    data: Record<string, unknown>[],
    options: ExportOptions
  ): Promise<void> => {
    updateProgress({
      status: 'generating',
      message: 'Generating CSV...',
      totalRows: data.length,
      currentRow: 0,
    });

    try {
      const content = generateCSV(data, options.columns, options.includeHeaders);
      const filename = `${options.filename}${getFileExtension('csv')}`;

      downloadFile(content, filename, getMimeType('csv'));

      updateProgress({
        status: 'complete',
        message: 'Export complete',
        currentRow: data.length,
      });

      hookOptions.onComplete?.();
    } catch (error) {
      updateProgress({
        status: 'error',
        message: error instanceof Error ? error.message : 'Export failed',
      });
      hookOptions.onError?.(error instanceof Error ? error : new Error('Export failed'));
      throw error;
    }
  }, [updateProgress, hookOptions]);

  // ============================================================================
  // Export to JSON
  // ============================================================================

  const exportToJSON = useCallback(async (
    data: Record<string, unknown>[],
    options: ExportOptions
  ): Promise<void> => {
    updateProgress({
      status: 'generating',
      message: 'Generating JSON...',
      totalRows: data.length,
      currentRow: 0,
    });

    try {
      const content = generateJSON(data);
      const filename = `${options.filename}${getFileExtension('json')}`;

      downloadFile(content, filename, getMimeType('json'));

      updateProgress({
        status: 'complete',
        message: 'Export complete',
        currentRow: data.length,
      });

      hookOptions.onComplete?.();
    } catch (error) {
      updateProgress({
        status: 'error',
        message: error instanceof Error ? error.message : 'Export failed',
      });
      hookOptions.onError?.(error instanceof Error ? error : new Error('Export failed'));
      throw error;
    }
  }, [updateProgress, hookOptions]);

  // ============================================================================
  // Export to Excel (XLSX)
  // ============================================================================

  const exportToExcel = useCallback(async (
    data: Record<string, unknown>[],
    options: ExportOptions
  ): Promise<void> => {
    updateProgress({
      status: 'preparing',
      message: 'Preparing Excel export...',
      totalRows: data.length,
      currentRow: 0,
    });

    try {
      // For Excel export, we'll generate a CSV that Excel can open
      // In a production app, you'd use a library like xlsx or exceljs
      const content = generateCSV(data, options.columns, options.includeHeaders);

      // Use tab-separated values for better Excel compatibility
      const tsvContent = content.replace(/,/g, '\t');
      const filename = `${options.filename}.xls`;

      // Create a Blob with Excel MIME type
      const blob = new Blob(['\ufeff' + tsvContent], {
        type: 'application/vnd.ms-excel;charset=utf-8;',
      });

      downloadFile(blob, filename, 'application/vnd.ms-excel');

      updateProgress({
        status: 'complete',
        message: 'Export complete',
        currentRow: data.length,
      });

      hookOptions.onComplete?.();
    } catch (error) {
      updateProgress({
        status: 'error',
        message: error instanceof Error ? error.message : 'Export failed',
      });
      hookOptions.onError?.(error instanceof Error ? error : new Error('Export failed'));
      throw error;
    }
  }, [updateProgress, hookOptions]);

  // ============================================================================
  // Export to PDF
  // ============================================================================

  const exportToPDF = useCallback(async (
    data: Record<string, unknown>[],
    options: ExportOptions
  ): Promise<void> => {
    updateProgress({
      status: 'preparing',
      message: 'Preparing PDF export...',
      totalRows: data.length,
      currentRow: 0,
    });

    try {
      // Generate HTML content for PDF
      const htmlContent = generatePDFHTML(data, options);

      // Create a new window with the content
      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        throw new Error('Please allow popups to export PDF');
      }

      printWindow.document.write(htmlContent);
      printWindow.document.close();

      // Wait for content to load then trigger print
      printWindow.onload = () => {
        printWindow.print();
        printWindow.close();
      };

      updateProgress({
        status: 'complete',
        message: 'PDF ready for printing',
        currentRow: data.length,
      });

      hookOptions.onComplete?.();
    } catch (error) {
      updateProgress({
        status: 'error',
        message: error instanceof Error ? error.message : 'Export failed',
      });
      hookOptions.onError?.(error instanceof Error ? error : new Error('Export failed'));
      throw error;
    }
  }, [updateProgress, hookOptions]);

  // ============================================================================
  // Generate PDF HTML
  // ============================================================================

  const generatePDFHTML = (
    data: Record<string, unknown>[],
    options: ExportOptions
  ): string => {
    const headerRow = options.columns
      .map(col => `<th style="border: 1px solid #ddd; padding: 8px; background: #f5f5f5; text-align: left;">${col.header}</th>`)
      .join('');

    const dataRows = data
      .map(row => {
        const cells = options.columns
          .map(col => {
            const value = getNestedValue(row, col.key);
            const formatted = formatExportValue(value, col.format);
            return `<td style="border: 1px solid #ddd; padding: 8px;">${escapeHTML(formatted)}</td>`;
          })
          .join('');
        return `<tr>${cells}</tr>`;
      })
      .join('');

    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${options.title || options.filename}</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      font-size: 12px;
      margin: 20px;
    }
    h1 {
      font-size: 18px;
      margin-bottom: 5px;
    }
    h2 {
      font-size: 14px;
      color: #666;
      margin-top: 0;
      margin-bottom: 20px;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    @media print {
      body {
        margin: 0;
      }
      table {
        font-size: 10px;
      }
    }
  </style>
</head>
<body>
  ${options.title ? `<h1>${escapeHTML(options.title)}</h1>` : ''}
  ${options.subtitle ? `<h2>${escapeHTML(options.subtitle)}</h2>` : ''}
  <table>
    <thead>
      <tr>${headerRow}</tr>
    </thead>
    <tbody>
      ${dataRows}
    </tbody>
  </table>
  <p style="margin-top: 20px; color: #666; font-size: 10px;">
    Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}
  </p>
</body>
</html>`;
  };

  // ============================================================================
  // Main Export Function
  // ============================================================================

  const exportData = useCallback(async (
    data: Record<string, unknown>[],
    options: ExportOptions
  ): Promise<void> => {
    if (!data || data.length === 0) {
      throw new Error('No data to export');
    }

    switch (options.format) {
      case 'csv':
        return exportToCSV(data, options);
      case 'json':
        return exportToJSON(data, options);
      case 'xlsx':
        return exportToExcel(data, options);
      case 'pdf':
        return exportToPDF(data, options);
      default:
        throw new Error(`Unsupported export format: ${options.format}`);
    }
  }, [exportToCSV, exportToJSON, exportToExcel, exportToPDF]);

  // ============================================================================
  // Reset Progress
  // ============================================================================

  const reset = useCallback(() => {
    setProgress({
      status: 'idle',
      currentRow: 0,
      totalRows: 0,
      message: '',
    });
  }, []);

  // ============================================================================
  // Return Hook API
  // ============================================================================

  return {
    // State
    progress,
    isExporting: ['preparing', 'generating'].includes(progress.status),
    isComplete: progress.status === 'complete',
    isError: progress.status === 'error',

    // Actions
    exportData,
    exportToCSV,
    exportToJSON,
    exportToExcel,
    exportToPDF,
    reset,

    // Column Configurations
    peopleColumns: PEOPLE_EXPORT_COLUMNS,
    assignmentColumns: ASSIGNMENT_EXPORT_COLUMNS,
    absenceColumns: ABSENCE_EXPORT_COLUMNS,
    scheduleColumns: SCHEDULE_EXPORT_COLUMNS,
  };
}

// ============================================================================
// Helper Functions
// ============================================================================

function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce((acc: unknown, key: string) => {
    if (acc && typeof acc === 'object' && key in acc) {
      return (acc as Record<string, unknown>)[key];
    }
    return undefined;
  }, obj);
}

function escapeHTML(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ============================================================================
// Export hook type
// ============================================================================

export type UseExportReturn = ReturnType<typeof useExport>;
