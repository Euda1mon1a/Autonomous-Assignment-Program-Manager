'use client';

/**
 * CSVImportModal Component
 *
 * Modal for importing rotation templates from a CSV file.
 * Supports column mapping, preview, and validation before import.
 */
import React, { useState, useCallback, useMemo, useRef } from 'react';
import {
  X,
  Upload,
  Download,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
} from 'lucide-react';
import type { TemplateCreateRequest } from '@/types/admin-templates';
import {
  parseCSV,
  autoDetectMapping,
  applyMappingAndValidate,
  toTemplateCreateRequests,
  generateSampleCSV,
  COLUMN_LABELS,
  REQUIRED_COLUMNS,
  type ColumnMapping,
  type CSVParseResult,
  type MappedTemplate,
} from '@/utils/csvParser';

// ============================================================================
// Types
// ============================================================================

export interface CSVImportModalProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Callback to close modal */
  onClose: () => void;
  /** Callback when templates are imported */
  onImport: (templates: TemplateCreateRequest[]) => Promise<void>;
  /** Whether import is in progress */
  isImporting?: boolean;
}

type ImportStep = 'upload' | 'mapping' | 'preview';

// ============================================================================
// Subcomponents
// ============================================================================

interface ColumnMappingSelectorProps {
  field: keyof ColumnMapping;
  label: string;
  value: string | null;
  headers: string[];
  required?: boolean;
  onChange: (value: string | null) => void;
}

function ColumnMappingSelector({
  field: _field,
  label,
  value,
  headers,
  required = false,
  onChange,
}: ColumnMappingSelectorProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-b-0">
      <div>
        <span className="text-sm text-white">{label}</span>
        {required && <span className="text-red-400 ml-1">*</span>}
      </div>
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value || null)}
        className={`w-48 px-3 py-1.5 bg-slate-700 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 ${
          required && !value
            ? 'border-red-500/50 text-red-300'
            : 'border-slate-600 text-white'
        }`}
      >
        <option value="">-- Not Mapped --</option>
        {headers.map((header) => (
          <option key={header} value={header}>
            {header}
          </option>
        ))}
      </select>
    </div>
  );
}

interface PreviewTableProps {
  templates: MappedTemplate[];
}

function PreviewTable({ templates }: PreviewTableProps) {
  const [showAll, setShowAll] = useState(false);
  const displayTemplates = showAll ? templates : templates.slice(0, 10);

  return (
    <div className="bg-slate-900/50 border border-slate-700 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-800 border-b border-slate-700">
              <th className="w-12 py-2 px-3 text-left text-slate-400 font-medium">
                Row
              </th>
              <th className="py-2 px-3 text-left text-slate-400 font-medium">
                Status
              </th>
              <th className="py-2 px-3 text-left text-slate-400 font-medium">
                Name
              </th>
              <th className="py-2 px-3 text-left text-slate-400 font-medium">
                Type
              </th>
              <th className="py-2 px-3 text-left text-slate-400 font-medium">
                Abbr
              </th>
              <th className="py-2 px-3 text-left text-slate-400 font-medium">
                Issues
              </th>
            </tr>
          </thead>
          <tbody>
            {displayTemplates.map((template) => (
              <tr
                key={template._rowIndex}
                className={`border-b border-slate-700/50 ${
                  template._errors.length > 0 ? 'bg-red-500/5' : ''
                }`}
              >
                <td className="py-2 px-3 text-slate-500">{template._rowIndex}</td>
                <td className="py-2 px-3">
                  {template._errors.length > 0 ? (
                    <XCircle className="w-4 h-4 text-red-400" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  )}
                </td>
                <td className="py-2 px-3 text-white">{template.name || '-'}</td>
                <td className="py-2 px-3 text-slate-300">{template.activityType}</td>
                <td className="py-2 px-3 text-slate-300">
                  {template.abbreviation || '-'}
                </td>
                <td className="py-2 px-3">
                  {template._errors.length > 0 && (
                    <span className="text-xs text-red-400">
                      {template._errors.join('; ')}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {templates.length > 10 && (
        <div className="p-2 border-t border-slate-700 text-center">
          <button
            type="button"
            onClick={() => setShowAll(!showAll)}
            className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
          >
            {showAll
              ? 'Show less'
              : `Show all ${templates.length} rows`}
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function CSVImportModal({
  isOpen,
  onClose,
  onImport,
  isImporting = false,
}: CSVImportModalProps) {
  const [step, setStep] = useState<ImportStep>('upload');
  const [parseResult, setParseResult] = useState<CSVParseResult | null>(null);
  const [mapping, setMapping] = useState<ColumnMapping | null>(null);
  const [validatedTemplates, setValidatedTemplates] = useState<MappedTemplate[]>([]);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validCount = useMemo(
    () => validatedTemplates.filter((t) => t._errors.length === 0).length,
    [validatedTemplates]
  );

  const handleFileSelect = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      const result = parseCSV(content);
      setParseResult(result);

      if (result.errors.length === 0 && result.headers.length > 0) {
        const autoMapping = autoDetectMapping(result.headers);
        setMapping(autoMapping);
        setStep('mapping');
      } else {
        setValidationErrors(result.errors.map((err) => err.message));
      }
    };
    reader.readAsText(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);

      const file = e.dataTransfer.files[0];
      if (file && (file.type === 'text/csv' || file.name.endsWith('.csv'))) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const handleMappingChange = useCallback(
    (field: keyof ColumnMapping, value: string | null) => {
      if (!mapping) return;
      setMapping({ ...mapping, [field]: value });
    },
    [mapping]
  );

  const handleApplyMapping = useCallback(() => {
    if (!parseResult || !mapping) return;

    const result = applyMappingAndValidate(parseResult.rows, mapping);
    setValidatedTemplates(result.templates);
    setValidationErrors(result.errors.map((e) => e.message));
    setStep('preview');
  }, [parseResult, mapping]);

  const handleImport = useCallback(async () => {
    if (validCount === 0) return;

    const templates = toTemplateCreateRequests(validatedTemplates);
    await onImport(templates);
  }, [validatedTemplates, validCount, onImport]);

  const handleDownloadSample = useCallback(() => {
    const csv = generateSampleCSV();
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'template-import-sample.csv';
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleClose = useCallback(() => {
    if (isImporting) return;
    onClose();
    // Reset state
    setStep('upload');
    setParseResult(null);
    setMapping(null);
    setValidatedTemplates([]);
    setValidationErrors([]);
  }, [isImporting, onClose]);

  const handleBack = useCallback(() => {
    if (step === 'preview') {
      setStep('mapping');
    } else if (step === 'mapping') {
      setStep('upload');
      setParseResult(null);
      setMapping(null);
    }
  }, [step]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="csv-import-title"
    >
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div>
            <h2 id="csv-import-title" className="text-lg font-semibold text-white">
              Import Templates from CSV
            </h2>
            <p className="text-sm text-slate-400 mt-0.5">
              {step === 'upload' && 'Upload a CSV file with template data'}
              {step === 'mapping' && 'Map CSV columns to template fields'}
              {step === 'preview' && 'Review and import templates'}
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={isImporting}
            className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Step 1: Upload */}
          {step === 'upload' && (
            <div className="space-y-4">
              <div
                className={`
                  border-2 border-dashed rounded-xl p-8 text-center transition-colors
                  ${
                    dragActive
                      ? 'border-violet-500 bg-violet-500/10'
                      : 'border-slate-600 hover:border-slate-500'
                  }
                `}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
              >
                <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <p className="text-white font-medium mb-2">
                  Drag and drop your CSV file here
                </p>
                <p className="text-slate-400 text-sm mb-4">or</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,text/csv"
                  onChange={handleInputChange}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  <Upload className="w-4 h-4 inline-block mr-2" />
                  Browse Files
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
                <div>
                  <p className="text-sm text-white font-medium">
                    Need a template?
                  </p>
                  <p className="text-xs text-slate-400">
                    Download a sample CSV with the correct format
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleDownloadSample}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-violet-400 hover:text-violet-300 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Download Sample
                </button>
              </div>

              {validationErrors.length > 0 && (
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-red-400">
                        Error parsing CSV
                      </p>
                      <ul className="text-sm text-red-300 mt-1 space-y-0.5">
                        {validationErrors.map((error, i) => (
                          <li key={i}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Mapping */}
          {step === 'mapping' && parseResult && mapping && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-900/50 rounded-lg">
                <p className="text-sm text-slate-300 mb-4">
                  Found <span className="text-white font-medium">{parseResult.rows.length}</span> rows
                  and <span className="text-white font-medium">{parseResult.headers.length}</span> columns.
                  Map CSV columns to template fields below.
                </p>

                <div className="space-y-1">
                  {(Object.keys(COLUMN_LABELS) as (keyof ColumnMapping)[]).map((field) => (
                    <ColumnMappingSelector
                      key={field}
                      field={field}
                      label={COLUMN_LABELS[field]}
                      value={mapping[field]}
                      headers={parseResult.headers}
                      required={REQUIRED_COLUMNS.includes(field)}
                      onChange={(value) => handleMappingChange(field, value)}
                    />
                  ))}
                </div>
              </div>

              {validationErrors.length > 0 && (
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <ul className="text-sm text-red-300">
                      {validationErrors.map((error, i) => (
                        <li key={i}>{error}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Preview */}
          {step === 'preview' && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="flex items-center gap-4 p-4 bg-slate-900/50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="text-emerald-400 font-medium">{validCount} valid</span>
                </div>
                {validatedTemplates.length - validCount > 0 && (
                  <div className="flex items-center gap-2">
                    <XCircle className="w-5 h-5 text-red-400" />
                    <span className="text-red-400 font-medium">
                      {validatedTemplates.length - validCount} invalid
                    </span>
                  </div>
                )}
              </div>

              {/* Preview table */}
              <PreviewTable templates={validatedTemplates} />

              {validCount === 0 && (
                <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-amber-300">
                      No valid templates to import. Please fix the errors and try again.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-slate-700">
          <div>
            {step !== 'upload' && (
              <button
                type="button"
                onClick={handleBack}
                disabled={isImporting}
                className="px-4 py-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
              >
                Back
              </button>
            )}
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={isImporting}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            {step === 'mapping' && (
              <button
                type="button"
                onClick={handleApplyMapping}
                disabled={!REQUIRED_COLUMNS.every((c) => mapping?.[c])}
                className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Preview Import
                <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
              </button>
            )}

            {step === 'preview' && (
              <button
                type="button"
                onClick={handleImport}
                disabled={validCount === 0 || isImporting}
                className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isImporting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Import {validCount} Template{validCount !== 1 ? 's' : ''}
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CSVImportModal;
