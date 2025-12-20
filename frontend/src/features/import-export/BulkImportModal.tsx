'use client';

/**
 * Bulk import modal for CSV/Excel data import
 */

import { useState, useCallback, useRef, useId } from 'react';
import { X, Upload, FileText, AlertCircle, CheckCircle, Download } from 'lucide-react';
import { useImport } from './useImport';
import { ImportPreview } from './ImportPreview';
import { ImportProgressIndicator } from './ImportProgressIndicator';
import type { ImportDataType, ImportOptions } from './types';

// ============================================================================
// Types
// ============================================================================

interface BulkImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  defaultDataType?: ImportDataType;
  title?: string;
}

type ImportStep = 'upload' | 'preview' | 'importing' | 'complete';

// ============================================================================
// Component
// ============================================================================

export function BulkImportModal({
  isOpen,
  onClose,
  onSuccess,
  defaultDataType = 'schedules',
  title = 'Bulk Import',
}: BulkImportModalProps) {
  const titleId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState<ImportStep>('upload');
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  const {
    file,
    dataType,
    preview,
    progress,
    options,
    isLoading,
    previewImport,
    executeImport,
    cancelImport,
    reset,
    updateOptions,
    setDataType,
  } = useImport({
    dataType: defaultDataType,
    onComplete: () => {
      setStep('complete');
      onSuccess?.();
    },
    onError: (error) => {
      setFileError(error.message);
    },
  });

  // ============================================================================
  // File Handling
  // ============================================================================

  const handleFileSelect = useCallback(async (selectedFile: File) => {
    setFileError(null);

    // Validate file type
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/json',
    ];
    const validExtensions = ['.csv', '.xlsx', '.xls', '.json'];

    const isValidType = validTypes.includes(selectedFile.type) ||
      validExtensions.some(ext => selectedFile.name.toLowerCase().endsWith(ext));

    if (!isValidType) {
      setFileError('Please select a CSV, Excel, or JSON file');
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (selectedFile.size > maxSize) {
      setFileError('File size exceeds 10MB limit');
      return;
    }

    try {
      await previewImport(selectedFile);
      setStep('preview');
    } catch (error) {
      setFileError(error instanceof Error ? error.message : 'Failed to parse file');
    }
  }, [previewImport]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  }, [handleFileSelect]);

  // ============================================================================
  // Actions
  // ============================================================================

  const handleStartImport = useCallback(async () => {
    setStep('importing');
    try {
      await executeImport();
    } catch (error) {
      // Error handled by hook
      console.error('Import failed:', error);
    }
  }, [executeImport]);

  const handleClose = useCallback(() => {
    if (isLoading) {
      cancelImport();
    }
    reset();
    setStep('upload');
    setFileError(null);
    onClose();
  }, [isLoading, cancelImport, reset, onClose]);

  const handleBack = useCallback(() => {
    reset();
    setStep('upload');
    setFileError(null);
  }, [reset]);

  const handleDownloadTemplate = useCallback(() => {
    // Generate sample CSV template based on data type
    const templates: Record<ImportDataType, string> = {
      people: 'name,email,type,pgy_level,performs_procedures,specialties,primary_duty\nJohn Doe,john.doe@example.com,resident,2,true,"cardiology",Outpatient\nJane Smith,jane.smith@example.com,faculty,,false,"internal medicine",Attending',
      assignments: 'date,time_of_day,person_name,rotation_name,role,activity_override,notes\n2025-01-15,AM,John Doe,Clinic,primary,,\n2025-01-15,PM,Jane Smith,Procedures,supervising,,',
      absences: 'person_name,start_date,end_date,absence_type,deployment_orders,tdy_location,notes\nJohn Doe,2025-01-20,2025-01-24,vacation,false,,Annual leave\nJane Smith,2025-02-01,2025-02-15,deployment,true,Fort Bragg,Military deployment',
      schedules: 'date,time_of_day,person_name,rotation_name,role,activity_override\n2025-01-15,AM,John Doe,Morning Clinic,primary,\n2025-01-15,AM,Jane Smith,Morning Clinic,supervising,',
    };

    const content = templates[dataType];
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${dataType}_import_template.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [dataType]);

  // ============================================================================
  // Render
  // ============================================================================

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative bg-white rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[90vh] flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b flex-shrink-0">
          <h2 id={titleId} className="text-lg font-semibold">{title}</h2>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-gray-100 rounded"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {/* Upload Step */}
          {step === 'upload' && (
            <div className="space-y-6">
              {/* Data Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  What are you importing?
                </label>
                <select
                  value={dataType}
                  onChange={(e) => setDataType(e.target.value as ImportDataType)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="schedules">Schedule / Assignments</option>
                  <option value="people">People (Residents & Faculty)</option>
                  <option value="absences">Absences</option>
                  <option value="assignments">Individual Assignments</option>
                </select>
              </div>

              {/* File Drop Zone */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`
                  border-2 border-dashed rounded-lg p-8 text-center transition-colors
                  ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
                  ${fileError ? 'border-red-300 bg-red-50' : ''}
                `}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls,.json"
                  onChange={handleFileInputChange}
                  className="hidden"
                />

                <Upload className={`w-12 h-12 mx-auto mb-4 ${dragActive ? 'text-blue-500' : 'text-gray-400'}`} />

                <p className="text-lg font-medium text-gray-700 mb-2">
                  Drag and drop your file here
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  or click to browse
                </p>

                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="btn-primary"
                  disabled={isLoading}
                >
                  Select File
                </button>

                <p className="text-xs text-gray-400 mt-4">
                  Supported formats: CSV, Excel (.xlsx, .xls), JSON
                </p>
              </div>

              {/* File Error */}
              {fileError && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-md text-red-700">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span>{fileError}</span>
                </div>
              )}

              {/* Download Template */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-700">Need a template?</p>
                  <p className="text-sm text-gray-500">
                    Download a sample CSV file with the correct format
                  </p>
                </div>
                <button
                  onClick={handleDownloadTemplate}
                  className="btn-secondary flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download Template
                </button>
              </div>
            </div>
          )}

          {/* Preview Step */}
          {step === 'preview' && preview && (
            <div className="space-y-6">
              {/* File Info */}
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <FileText className="w-6 h-6 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-700">{file?.name}</p>
                  <p className="text-sm text-gray-500">
                    {preview.totalRows} rows detected as {dataType}
                  </p>
                </div>
              </div>

              {/* Import Options */}
              <div className="p-4 border border-gray-200 rounded-lg space-y-3">
                <h3 className="font-medium text-gray-700">Import Options</h3>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={options.skipDuplicates}
                      onChange={(e) => updateOptions({ skipDuplicates: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-600">Skip duplicate entries</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={options.updateExisting}
                      onChange={(e) => updateOptions({ updateExisting: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-600">Update existing records</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={options.skipInvalidRows}
                      onChange={(e) => updateOptions({ skipInvalidRows: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-600">Skip invalid rows</span>
                  </label>
                </div>
              </div>

              {/* Preview Table */}
              <ImportPreview preview={preview} maxDisplayRows={50} />

              {/* Validation Summary */}
              {preview.errorRows > 0 && (
                <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-800">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">Validation Issues Found</p>
                    <p className="text-sm">
                      {preview.errorRows} rows have errors and will be skipped.
                      {preview.warningRows > 0 && ` ${preview.warningRows} rows have warnings.`}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Importing Step */}
          {step === 'importing' && (
            <div className="py-8">
              <ImportProgressIndicator progress={progress} />
            </div>
          )}

          {/* Complete Step */}
          {step === 'complete' && (
            <div className="py-8 text-center space-y-4">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
              <h3 className="text-xl font-semibold text-gray-800">Import Complete!</h3>
              <p className="text-gray-600">
                Successfully imported {progress.successCount} records.
                {progress.errorCount > 0 && ` ${progress.errorCount} records failed.`}
                {progress.warningCount > 0 && ` ${progress.warningCount} records had warnings.`}
              </p>
              {progress.errors.length > 0 && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-left max-h-40 overflow-y-auto">
                  <p className="text-sm font-medium text-red-800 mb-2">Errors:</p>
                  <ul className="text-sm text-red-700 list-disc list-inside">
                    {progress.errors.slice(0, 10).map((error, index) => (
                      <li key={index}>Row {error.row}: {error.message}</li>
                    ))}
                    {progress.errors.length > 10 && (
                      <li>...and {progress.errors.length - 10} more</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t bg-gray-50 flex-shrink-0">
          <div>
            {step === 'preview' && (
              <button onClick={handleBack} className="btn-secondary">
                Back
              </button>
            )}
          </div>
          <div className="flex gap-3">
            <button onClick={handleClose} className="btn-secondary">
              {step === 'complete' ? 'Close' : 'Cancel'}
            </button>
            {step === 'preview' && preview && (
              <button
                onClick={handleStartImport}
                disabled={preview.validRows === 0 || isLoading}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Import {preview.validRows} Records
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
