'use client';

/**
 * AuditLogExport Component
 *
 * Provides export functionality for audit logs in multiple formats
 * (CSV, JSON, PDF) with configurable options.
 */

import { useState, useCallback } from 'react';
import { format } from 'date-fns';
import {
  Download,
  FileText,
  FileJson,
  FileSpreadsheet,
  X,
  Settings,
  Loader2,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { downloadFile, exportToCSV, exportToJSON, Column } from '@/lib/export';
import type {
  AuditLogEntry,
  AuditLogFilters,
  ExportFormat,
  AuditExportConfig,
} from './types';
import {
  ENTITY_TYPE_LABELS,
  ACTION_TYPE_LABELS,
} from './types';

// ============================================================================
// Types
// ============================================================================

interface AuditLogExportProps {
  logs: AuditLogEntry[];
  filters?: AuditLogFilters;
  totalCount: number;
  onExportAll?: (config: AuditExportConfig) => Promise<Blob>;
}

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (config: AuditExportConfig) => void;
  isExporting: boolean;
  exportStatus?: 'success' | 'error';
  errorMessage?: string;
}

// ============================================================================
// Constants
// ============================================================================

const EXPORT_FORMATS: Array<{
  format: ExportFormat;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  {
    format: 'csv',
    label: 'CSV',
    description: 'Spreadsheet compatible format',
    icon: FileSpreadsheet,
  },
  {
    format: 'json',
    label: 'JSON',
    description: 'Full data with nested objects',
    icon: FileJson,
  },
  {
    format: 'pdf',
    label: 'PDF',
    description: 'Formatted report document',
    icon: FileText,
  },
];

const CSV_COLUMNS: Column[] = [
  { key: 'timestamp', header: 'Timestamp' },
  { key: 'user.name', header: 'User' },
  { key: 'user.email', header: 'User Email' },
  { key: 'action', header: 'Action' },
  { key: 'entityType', header: 'Entity Type' },
  { key: 'entityId', header: 'Entity ID' },
  { key: 'entityName', header: 'Entity Name' },
  { key: 'severity', header: 'Severity' },
  { key: 'reason', header: 'Reason' },
  { key: 'acgmeOverride', header: 'ACGME Override' },
  { key: 'acgmeJustification', header: 'ACGME Justification' },
  { key: 'ipAddress', header: 'IP Address' },
];

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Transform audit log entry for export
 */
function transformForExport(
  log: AuditLogEntry,
  includeChanges: boolean = false
): Record<string, unknown> {
  const base = {
    id: log.id,
    timestamp: format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss'),
    user: log.user,
    action: ACTION_TYPE_LABELS[log.action] || log.action,
    entityType: ENTITY_TYPE_LABELS[log.entityType] || log.entityType,
    entityId: log.entityId,
    entityName: log.entityName || '',
    severity: log.severity,
    reason: log.reason || '',
    acgmeOverride: log.acgmeOverride ? 'Yes' : 'No',
    acgmeJustification: log.acgmeJustification || '',
    ipAddress: log.ipAddress || '',
  };

  if (includeChanges && log.changes) {
    return {
      ...base,
      changes: log.changes.map((c) => ({
        field: c.field,
        oldValue: c.oldValue,
        newValue: c.newValue,
      })),
    };
  }

  return base;
}

/**
 * Generate filename for export
 */
function generateFilename(
  format: ExportFormat,
  filters?: AuditLogFilters
): string {
  const dateStr = format === 'pdf'
    ? format.replace(/\//g, '-')
    : format(new Date(), 'yyyy-MM-dd_HHmmss');

  let suffix = '';
  if (filters?.dateRange) {
    suffix = `_${filters.dateRange.start}_to_${filters.dateRange.end}`;
  }

  return `audit_log${suffix}_${dateStr}.${format}`;
}

/**
 * Export logs to CSV format
 */
function exportLogsToCSV(logs: AuditLogEntry[], filename: string): void {
  const transformedLogs = logs.map((log) => ({
    ...transformForExport(log),
    'user.name': log.user.name,
    'user.email': log.user.email || '',
  }));

  exportToCSV(transformedLogs, filename, CSV_COLUMNS);
}

/**
 * Export logs to JSON format
 */
function exportLogsToJSON(
  logs: AuditLogEntry[],
  filename: string,
  includeChanges: boolean = true
): void {
  const transformedLogs = logs.map((log) => transformForExport(log, includeChanges));
  exportToJSON(transformedLogs, filename);
}

/**
 * Generate PDF report content (returns HTML for printing)
 */
function generatePDFContent(logs: AuditLogEntry[], filters?: AuditLogFilters): string {
  const dateStr = format(new Date(), 'MMMM d, yyyy');

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Audit Log Report</title>
      <style>
        body { font-family: Arial, sans-serif; font-size: 12px; margin: 20px; }
        h1 { font-size: 18px; margin-bottom: 10px; }
        .meta { color: #666; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f5f5f5; }
        .severity-info { color: #2563eb; }
        .severity-warning { color: #d97706; }
        .severity-critical { color: #dc2626; }
        .acgme-override { background-color: #fff7ed; }
        @media print {
          table { page-break-inside: auto; }
          tr { page-break-inside: avoid; }
        }
      </style>
    </head>
    <body>
      <h1>Audit Log Report</h1>
      <div class="meta">
        <p>Generated: ${dateStr}</p>
        <p>Total Records: ${logs.length}</p>
        ${filters?.dateRange ? `<p>Date Range: ${filters.dateRange.start} to ${filters.dateRange.end}</p>` : ''}
      </div>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>User</th>
            <th>Action</th>
            <th>Entity</th>
            <th>Severity</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          ${logs
            .map(
              (log) => `
              <tr class="${log.acgmeOverride ? 'acgme-override' : ''}">
                <td>${format(new Date(log.timestamp), 'MMM d, yyyy HH:mm')}</td>
                <td>${log.user.name}</td>
                <td>${ACTION_TYPE_LABELS[log.action] || log.action}</td>
                <td>${ENTITY_TYPE_LABELS[log.entityType]} ${log.entityName ? `(${log.entityName})` : ''}</td>
                <td class="severity-${log.severity}">${log.severity}</td>
                <td>${log.reason || '-'}</td>
              </tr>
            `
            )
            .join('')}
        </tbody>
      </table>
    </body>
    </html>
  `;
}

// ============================================================================
// Export Modal Component
// ============================================================================

function ExportModal({
  isOpen,
  onClose,
  onExport,
  isExporting,
  exportStatus,
  errorMessage,
}: ExportModalProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('csv');
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [includeChanges, setIncludeChanges] = useState(true);

  if (!isOpen) return null;

  const handleExport = () => {
    onExport({
      format: selectedFormat,
      includeMetadata,
      includeChanges,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Export Audit Logs</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {/* Format selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Format
            </label>
            <div className="grid grid-cols-3 gap-2">
              {EXPORT_FORMATS.map(({ format, label, description, icon: Icon }) => (
                <button
                  key={format}
                  type="button"
                  onClick={() => setSelectedFormat(format)}
                  className={`
                    flex flex-col items-center p-3 border rounded-lg transition-colors
                    ${
                      selectedFormat === format
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:bg-gray-50'
                    }
                  `}
                >
                  <Icon
                    className={`w-6 h-6 mb-1 ${
                      selectedFormat === format ? 'text-blue-600' : 'text-gray-500'
                    }`}
                  />
                  <span className="text-sm font-medium">{label}</span>
                  <span className="text-xs text-gray-500 text-center mt-1">
                    {description}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="border-t pt-4">
            <div className="flex items-center gap-2 mb-2">
              <Settings className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Options</span>
            </div>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeMetadata}
                  onChange={(e) => setIncludeMetadata(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Include metadata (IP, user agent)</span>
              </label>
              {selectedFormat === 'json' && (
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeChanges}
                    onChange={(e) => setIncludeChanges(e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Include change details</span>
                </label>
              )}
            </div>
          </div>

          {/* Status messages */}
          {exportStatus === 'success' && (
            <div className="flex items-center gap-2 p-3 bg-green-50 text-green-700 rounded-lg">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm">Export completed successfully!</span>
            </div>
          )}

          {exportStatus === 'error' && (
            <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm">{errorMessage || 'Export failed. Please try again.'}</span>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 p-4 border-t bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExporting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Export
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function AuditLogExport({
  logs,
  filters,
  totalCount,
  onExportAll,
}: AuditLogExportProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState<'success' | 'error' | undefined>();
  const [errorMessage, setErrorMessage] = useState<string>();

  const handleExport = useCallback(
    async (config: AuditExportConfig) => {
      setIsExporting(true);
      setExportStatus(undefined);
      setErrorMessage(undefined);

      try {
        const filename = generateFilename(config.format, filters);

        // If exporting all records via API
        if (onExportAll && totalCount > logs.length) {
          const blob = await onExportAll(config);
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        } else {
          // Export current page data
          switch (config.format) {
            case 'csv':
              exportLogsToCSV(logs, filename);
              break;
            case 'json':
              exportLogsToJSON(logs, filename, config.includeChanges);
              break;
            case 'pdf':
              const htmlContent = generatePDFContent(logs, filters);
              const printWindow = window.open('', '_blank');
              if (printWindow) {
                printWindow.document.write(htmlContent);
                printWindow.document.close();
                printWindow.print();
              }
              break;
          }
        }

        setExportStatus('success');
        setTimeout(() => {
          setIsModalOpen(false);
          setExportStatus(undefined);
        }, 1500);
      } catch (error) {
        setExportStatus('error');
        setErrorMessage(
          error instanceof Error ? error.message : 'An unexpected error occurred'
        );
      } finally {
        setIsExporting(false);
      }
    },
    [logs, filters, totalCount, onExportAll]
  );

  const handleQuickExport = useCallback(
    (format: ExportFormat) => {
      handleExport({ format, includeMetadata: true, includeChanges: true });
    },
    [handleExport]
  );

  return (
    <>
      <div className="flex items-center gap-2">
        {/* Quick export buttons */}
        <div className="hidden sm:flex items-center gap-1">
          <button
            type="button"
            onClick={() => handleQuickExport('csv')}
            className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Export as CSV"
          >
            <FileSpreadsheet className="w-4 h-4" />
            CSV
          </button>
          <button
            type="button"
            onClick={() => handleQuickExport('json')}
            className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Export as JSON"
          >
            <FileJson className="w-4 h-4" />
            JSON
          </button>
        </div>

        {/* Full export button */}
        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          <Download className="w-4 h-4" />
          Export
          {totalCount > logs.length && (
            <span className="text-xs bg-blue-500 px-1.5 py-0.5 rounded">
              All {totalCount}
            </span>
          )}
        </button>
      </div>

      <ExportModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setExportStatus(undefined);
        }}
        onExport={handleExport}
        isExporting={isExporting}
        exportStatus={exportStatus}
        errorMessage={errorMessage}
      />
    </>
  );
}
