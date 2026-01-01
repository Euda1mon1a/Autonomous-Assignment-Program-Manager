'use client';

/**
 * Export panel component for exporting data to multiple formats
 */

import { useState, useCallback, useRef, useEffect, useId } from 'react';
import {
  Download,
  FileText,
  FileSpreadsheet,
  FileJson,
  Printer,
  ChevronDown,
  Loader2,
  Check,
  X,
  Settings2,
} from 'lucide-react';
import { useExport } from './useExport';
import type { ExportFormat, ExportColumn, ExportOptions } from './types';

// ============================================================================
// Types
// ============================================================================

interface ExportPanelProps {
  data: Record<string, unknown>[];
  columns: ExportColumn[];
  filename: string;
  title?: string;
  subtitle?: string;
  disabled?: boolean;
  className?: string;
  variant?: 'button' | 'dropdown' | 'panel';
  availableFormats?: ExportFormat[];
  onExportComplete?: () => void;
  onExportError?: (error: Error) => void;
}

// ============================================================================
// Format Icons
// ============================================================================

const FormatIcons: Record<ExportFormat, React.ComponentType<{ className?: string }>> = {
  csv: FileText,
  xlsx: FileSpreadsheet,
  json: FileJson,
  pdf: Printer,
};

const FormatLabels: Record<ExportFormat, string> = {
  csv: 'CSV',
  xlsx: 'Excel',
  json: 'JSON',
  pdf: 'PDF',
};

const FormatDescriptions: Record<ExportFormat, string> = {
  csv: 'Comma-separated values, compatible with Excel',
  xlsx: 'Microsoft Excel spreadsheet format',
  json: 'JavaScript Object Notation, for developers',
  pdf: 'Printable document format',
};

// ============================================================================
// Main Component
// ============================================================================

export function ExportPanel({
  data,
  columns,
  filename,
  title,
  subtitle,
  disabled = false,
  className = '',
  variant = 'dropdown',
  availableFormats = ['csv', 'xlsx', 'json', 'pdf'],
  onExportComplete,
  onExportError,
}: ExportPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('csv');
  const [includeHeaders, setIncludeHeaders] = useState(true);
  const [showOptions, setShowOptions] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const titleId = useId();

  const {
    progress,
    isExporting,
    isComplete,
    exportData,
    reset,
  } = useExport({
    onComplete: onExportComplete,
    onError: onExportError,
  });

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen]);

  // Reset on complete
  useEffect(() => {
    if (isComplete) {
      const timer = setTimeout(() => {
        reset();
        setIsOpen(false);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [isComplete, reset]);

  // Handle export
  const handleExport = useCallback(async (format: ExportFormat) => {
    const options: ExportOptions = {
      format,
      filename,
      columns,
      includeHeaders,
      dateFormat: 'YYYY-MM-DD',
      title,
      subtitle,
    };

    try {
      await exportData(data, options);
    } catch (error) {
      // Error handled by hook
      // console.error('Export failed:', error);
    }
  }, [data, columns, filename, title, subtitle, includeHeaders, exportData]);

  // Quick export (for button variant)
  const handleQuickExport = useCallback(() => {
    handleExport(selectedFormat);
  }, [handleExport, selectedFormat]);

  const isDisabled = disabled || !data || data.length === 0;

  // Button variant
  if (variant === 'button') {
    return (
      <button
        onClick={handleQuickExport}
        disabled={isDisabled || isExporting}
        className={`btn-secondary flex items-center gap-2 ${className}`}
        aria-label={`Export as ${FormatLabels[selectedFormat]}`}
      >
        {isExporting ? (
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
        ) : isComplete ? (
          <Check className="w-4 h-4 text-green-500" aria-hidden="true" />
        ) : (
          <Download className="w-4 h-4" aria-hidden="true" />
        )}
        Export
      </button>
    );
  }

  // Dropdown variant
  if (variant === 'dropdown') {
    return (
      <div className={`relative ${className}`} ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          disabled={isDisabled || isExporting}
          className="btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-haspopup="true"
          aria-expanded={isOpen}
          aria-label="Export data in various formats"
        >
          {isExporting ? (
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
          ) : isComplete ? (
            <Check className="w-4 h-4 text-green-500" aria-hidden="true" />
          ) : (
            <Download className="w-4 h-4" aria-hidden="true" />
          )}
          Export
          <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
        </button>

        {isOpen && (
          <div
            className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-10"
            role="menu"
          >
            {availableFormats.map((format) => {
              const Icon = FormatIcons[format];
              return (
                <button
                  key={format}
                  onClick={() => handleExport(format)}
                  disabled={isExporting}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none flex items-center gap-3 disabled:opacity-50"
                  role="menuitem"
                  aria-label={`Export as ${FormatLabels[format]}`}
                >
                  <Icon className="w-4 h-4 text-gray-400" aria-hidden="true" />
                  <span>Export as {FormatLabels[format]}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // Panel variant
  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h3 id={titleId} className="text-lg font-semibold text-gray-800">
          Export Data
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          {data.length} records available for export
        </p>
      </div>

      {/* Format Selection */}
      <div className="p-4 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {availableFormats.map((format) => {
            const Icon = FormatIcons[format];
            const isSelected = selectedFormat === format;

            return (
              <button
                key={format}
                onClick={() => setSelectedFormat(format)}
                disabled={isDisabled}
                className={`
                  p-4 rounded-lg border-2 transition-colors text-left
                  ${isSelected
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'}
                  ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
                `}
                role="radio"
                aria-checked={isSelected}
                aria-label={`Export as ${FormatLabels[format]}: ${FormatDescriptions[format]}`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-6 h-6 ${isSelected ? 'text-blue-500' : 'text-gray-400'}`} aria-hidden="true" />
                  <div>
                    <p className={`font-medium ${isSelected ? 'text-blue-700' : 'text-gray-700'}`}>
                      {FormatLabels[format]}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {FormatDescriptions[format]}
                    </p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Options Toggle */}
        <button
          onClick={() => setShowOptions(!showOptions)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
          aria-expanded={showOptions}
          aria-label="Toggle export options"
        >
          <Settings2 className="w-4 h-4" aria-hidden="true" />
          <span>Export Options</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${showOptions ? 'rotate-180' : ''}`} aria-hidden="true" />
        </button>

        {/* Options Panel */}
        {showOptions && (
          <div className="p-3 bg-gray-50 rounded-lg space-y-3">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeHeaders}
                onChange={(e) => setIncludeHeaders(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600">Include column headers</span>
            </label>

            {/* Column Selection */}
            <div>
              <p className="text-sm text-gray-600 mb-2">Columns to export:</p>
              <div className="flex flex-wrap gap-2">
                {columns.map((col) => (
                  <span
                    key={col.key}
                    className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-600"
                  >
                    {col.header}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Progress */}
        {isExporting && (
          <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg" role="status" aria-live="polite">
            <Loader2 className="w-4 h-4 text-blue-500 animate-spin" aria-hidden="true" />
            <span className="text-sm text-blue-700">{progress.message}</span>
          </div>
        )}

        {/* Success */}
        {isComplete && (
          <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg" role="status" aria-live="polite">
            <Check className="w-4 h-4 text-green-500" aria-hidden="true" />
            <span className="text-sm text-green-700">Export complete!</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <button
          onClick={() => handleExport(selectedFormat)}
          disabled={isDisabled || isExporting}
          className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={`Export as ${FormatLabels[selectedFormat]}`}
        >
          {isExporting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
              Exporting...
            </>
          ) : (
            <>
              <Download className="w-4 h-4" aria-hidden="true" />
              Export as {FormatLabels[selectedFormat]}
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// Quick Export Button
// ============================================================================

interface QuickExportButtonProps {
  data: Record<string, unknown>[];
  columns: ExportColumn[];
  filename: string;
  format?: ExportFormat;
  disabled?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export function QuickExportButton({
  data,
  columns,
  filename,
  format = 'csv',
  disabled = false,
  className = '',
  children,
}: QuickExportButtonProps) {
  const { exportData, isExporting, isComplete, reset } = useExport();
  const Icon = FormatIcons[format];

  useEffect(() => {
    if (isComplete) {
      const timer = setTimeout(reset, 1500);
      return () => clearTimeout(timer);
    }
  }, [isComplete, reset]);

  const handleClick = async () => {
    const options: ExportOptions = {
      format,
      filename,
      columns,
      includeHeaders: true,
      dateFormat: 'YYYY-MM-DD',
    };

    try {
      await exportData(data, options);
    } catch (error) {
      // Error handled by hook
      // console.error('Export failed:', error);
    }
  };

  const isDisabled = disabled || !data || data.length === 0;

  return (
    <button
      onClick={handleClick}
      disabled={isDisabled || isExporting}
      className={`btn-secondary flex items-center gap-2 ${className}`}
      aria-label={`Export ${FormatLabels[format]}`}
    >
      {isExporting ? (
        <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
      ) : isComplete ? (
        <Check className="w-4 h-4 text-green-500" aria-hidden="true" />
      ) : (
        <Icon className="w-4 h-4" aria-hidden="true" />
      )}
      {children || `Export ${FormatLabels[format]}`}
    </button>
  );
}

// ============================================================================
// Export Modal
// ============================================================================

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: Record<string, unknown>[];
  columns: ExportColumn[];
  filename: string;
  title?: string;
  subtitle?: string;
}

export function ExportModal({
  isOpen,
  onClose,
  data,
  columns,
  filename,
  title,
  subtitle,
}: ExportModalProps) {
  const titleId = useId();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4"
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded"
          aria-label="Close export modal"
        >
          <X className="w-5 h-5" aria-hidden="true" />
        </button>

        {/* Export Panel */}
        <ExportPanel
          data={data}
          columns={columns}
          filename={filename}
          title={title}
          subtitle={subtitle}
          variant="panel"
          onExportComplete={onClose}
        />
      </div>
    </div>
  );
}
