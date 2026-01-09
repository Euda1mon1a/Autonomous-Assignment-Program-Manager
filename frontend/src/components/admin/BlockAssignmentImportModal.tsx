'use client';

/**
 * BlockAssignmentImportModal Component
 *
 * Multi-step wizard for importing block assignments from CSV/Excel.
 * Steps: Upload -> Preview -> Import -> Complete
 *
 * Features:
 * - File upload or paste CSV content
 * - Preview with color-coded match status
 * - Inline rotation template creation for unknowns
 * - Duplicate handling (skip/update toggle)
 * - PERSEC compliant (anonymized names)
 */
import React, { useState, useCallback, useRef } from 'react';
import {
  Upload,
  Download,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  Plus,
  ChevronLeft,
  ArrowRight,
} from 'lucide-react';
import { Modal } from '@/components/Modal';
import { Button } from '@/components/ui/Button';
import { useBlockAssignmentImport } from '@/hooks/useBlockAssignmentImport';
import {
  DuplicateAction,
  MATCH_STATUS_COLORS,
  MATCH_STATUS_LABELS,
} from '@/types/block-assignment-import';
import type {
  BlockAssignmentPreviewItem,
  UnknownRotationItem,
  QuickTemplateCreateRequest,
} from '@/types/block-assignment-import';

// ============================================================================
// Props
// ============================================================================

export interface BlockAssignmentImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

// ============================================================================
// Activity Type Options
// ============================================================================

const ACTIVITY_TYPE_OPTIONS = [
  { value: 'clinic', label: 'Clinic' },
  { value: 'inpatient', label: 'Inpatient' },
  { value: 'outpatient', label: 'Outpatient' },
  { value: 'procedures', label: 'Procedures' },
  { value: 'call', label: 'Call' },
  { value: 'education', label: 'Education' },
  { value: 'off', label: 'Off' },
  { value: 'conference', label: 'Conference' },
];

// ============================================================================
// Component
// ============================================================================

export function BlockAssignmentImportModal({
  isOpen,
  onClose,
  onSuccess,
}: BlockAssignmentImportModalProps) {
  const {
    step,
    isLoading,
    error,
    preview,
    result,
    duplicateActions,
    canImport,
    matchedCount,
    errorCount,
    uploadContent,
    uploadFile,
    setDuplicateAction,
    setAllDuplicateActions,
    createTemplate,
    executeImport,
    downloadTemplate,
    reset,
    goBack,
  } = useBlockAssignmentImport();

  // Local state for upload step
  const [csvContent, setCsvContent] = useState('');
  const [academicYear, setAcademicYear] = useState<number | undefined>();
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Quick template dialog state
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [templateAbbrev, setTemplateAbbrev] = useState('');
  const [templateName, setTemplateName] = useState('');
  const [templateType, setTemplateType] = useState('outpatient');
  const [templateLeaveEligible, setTemplateLeaveEligible] = useState(true);

  // Handlers
  const handleClose = useCallback(() => {
    reset();
    setCsvContent('');
    setAcademicYear(undefined);
    onClose();
  }, [reset, onClose]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const file = e.dataTransfer.files?.[0];
      if (file) {
        await uploadFile(file, academicYear);
      }
    },
    [uploadFile, academicYear]
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        await uploadFile(file, academicYear);
      }
    },
    [uploadFile, academicYear]
  );

  const handlePasteUpload = useCallback(async () => {
    if (csvContent.trim()) {
      await uploadContent(csvContent, academicYear);
    }
  }, [uploadContent, csvContent, academicYear]);

  const handleOpenTemplateDialog = useCallback((abbrev: string) => {
    setTemplateAbbrev(abbrev);
    setTemplateName('');
    setTemplateType('outpatient');
    setTemplateLeaveEligible(true);
    setTemplateDialogOpen(true);
  }, []);

  const handleCreateTemplate = useCallback(async () => {
    const request: QuickTemplateCreateRequest = {
      abbreviation: templateAbbrev,
      name: templateName,
      activityType: templateType,
      leaveEligible: templateLeaveEligible,
    };
    await createTemplate(request);
    setTemplateDialogOpen(false);
    // Re-run preview to update match status
    if (csvContent) {
      await uploadContent(csvContent, academicYear);
    }
  }, [
    templateAbbrev,
    templateName,
    templateType,
    templateLeaveEligible,
    createTemplate,
    uploadContent,
    csvContent,
    academicYear,
  ]);

  const handleExecuteImport = useCallback(async () => {
    await executeImport(false);
    if (onSuccess) {
      onSuccess();
    }
  }, [executeImport, onSuccess]);

  // Render step content
  const renderUploadStep = () => (
    <div className="space-y-6">
      {/* Academic Year */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Academic Year (optional - auto-detected if empty)
        </label>
        <input
          type="number"
          value={academicYear ?? ''}
          onChange={(e) =>
            setAcademicYear(e.target.value ? parseInt(e.target.value) : undefined)
          }
          placeholder="e.g., 2025"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* File Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-600 mb-2">
          Drag and drop a CSV or Excel file here
        </p>
        <p className="text-sm text-gray-500 mb-4">or</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileSelect}
          className="hidden"
        />
        <Button
          variant="secondary"
          onClick={() => fileInputRef.current?.click()}
        >
          <FileSpreadsheet className="w-4 h-4 mr-2" />
          Select File
        </Button>
      </div>

      {/* Or Paste CSV */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Or paste CSV content
        </label>
        <textarea
          value={csvContent}
          onChange={(e) => setCsvContent(e.target.value)}
          placeholder="block_number,rotation_abbrev,resident_name&#10;1,HILO,Smith&#10;1,FMC,Jones"
          rows={6}
          className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <div className="mt-2 flex justify-between">
          <Button variant="ghost" size="sm" onClick={downloadTemplate}>
            <Download className="w-4 h-4 mr-1" />
            Download Template
          </Button>
          <Button
            onClick={handlePasteUpload}
            disabled={!csvContent.trim() || isLoading}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <ArrowRight className="w-4 h-4 mr-2" />
            )}
            Preview
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4 inline mr-2" />
          {error}
        </div>
      )}
    </div>
  );

  const renderPreviewStep = () => {
    if (!preview) return null;

    return (
      <div className="space-y-4">
        {/* Summary */}
        <div className="grid grid-cols-5 gap-2 text-sm">
          <div className="p-2 bg-gray-100 rounded text-center">
            <div className="font-semibold">{preview.totalRows}</div>
            <div className="text-gray-600">Total</div>
          </div>
          <div className="p-2 bg-green-100 rounded text-center">
            <div className="font-semibold text-green-700">{preview.matchedCount}</div>
            <div className="text-green-600">Matched</div>
          </div>
          <div className="p-2 bg-yellow-100 rounded text-center">
            <div className="font-semibold text-yellow-700">{preview.unknownRotationCount}</div>
            <div className="text-yellow-600">Unknown Rot.</div>
          </div>
          <div className="p-2 bg-red-100 rounded text-center">
            <div className="font-semibold text-red-700">{preview.unknownResidentCount}</div>
            <div className="text-red-600">Unknown Res.</div>
          </div>
          <div className="p-2 bg-gray-200 rounded text-center">
            <div className="font-semibold text-gray-700">{preview.duplicateCount}</div>
            <div className="text-gray-600">Duplicates</div>
          </div>
        </div>

        {/* Unknown Rotations - Quick Create */}
        {preview.unknownRotations.length > 0 && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <h4 className="font-medium text-yellow-800 mb-2 flex items-center">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Unknown Rotations ({preview.unknownRotations.length})
            </h4>
            <div className="space-y-2">
              {preview.unknownRotations.map((item) => (
                <div
                  key={item.abbreviation}
                  className="flex items-center justify-between text-sm"
                >
                  <span>
                    <strong>{item.abbreviation}</strong> ({item.occurrences} rows)
                    {item.suggestedName && (
                      <span className="text-gray-500 ml-2">
                        Suggested: {item.suggestedName}
                      </span>
                    )}
                  </span>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleOpenTemplateDialog(item.abbreviation)}
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    Create
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Duplicate Actions */}
        {preview.duplicateCount > 0 && (
          <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
            <h4 className="font-medium text-gray-800 mb-2">
              Duplicate Handling
            </h4>
            <div className="flex space-x-4 text-sm">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="duplicateAction"
                  checked={Object.values(duplicateActions).every(
                    (a) => a === DuplicateAction.SKIP
                  )}
                  onChange={() => setAllDuplicateActions(DuplicateAction.SKIP)}
                  className="mr-2"
                />
                Skip all duplicates
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="duplicateAction"
                  checked={Object.values(duplicateActions).every(
                    (a) => a === DuplicateAction.UPDATE
                  )}
                  onChange={() => setAllDuplicateActions(DuplicateAction.UPDATE)}
                  className="mr-2"
                />
                Update all duplicates
              </label>
            </div>
          </div>
        )}

        {/* Preview Table */}
        <div className="max-h-64 overflow-y-auto border rounded-md">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-3 py-2 text-left">Row</th>
                <th className="px-3 py-2 text-left">Block</th>
                <th className="px-3 py-2 text-left">Rotation</th>
                <th className="px-3 py-2 text-left">Resident</th>
                <th className="px-3 py-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {preview.items.slice(0, 50).map((item) => (
                <tr key={item.rowNumber} className="border-t">
                  <td className="px-3 py-2">{item.rowNumber}</td>
                  <td className="px-3 py-2">{item.blockNumber}</td>
                  <td className="px-3 py-2">
                    <span className="font-mono">{item.rotationInput}</span>
                    {item.matchedRotationName && (
                      <span className="text-gray-500 ml-1">
                        ({item.matchedRotationName})
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono">
                    {item.residentDisplay}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs ${
                        MATCH_STATUS_COLORS[item.matchStatus]
                      }`}
                    >
                      {MATCH_STATUS_LABELS[item.matchStatus]}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {preview.items.length > 50 && (
            <div className="p-2 bg-gray-50 text-center text-sm text-gray-500">
              Showing first 50 of {preview.items.length} rows
            </div>
          )}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            <AlertTriangle className="w-4 h-4 inline mr-2" />
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between pt-4 border-t">
          <Button variant="ghost" onClick={goBack}>
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back
          </Button>
          <Button onClick={handleExecuteImport} disabled={!canImport || isLoading}>
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle2 className="w-4 h-4 mr-2" />
            )}
            Import {matchedCount} Assignments
          </Button>
        </div>
      </div>
    );
  };

  const renderImportingStep = () => (
    <div className="py-12 text-center">
      <Loader2 className="w-12 h-12 mx-auto text-blue-500 animate-spin mb-4" />
      <p className="text-lg font-medium">Importing assignments...</p>
      <p className="text-sm text-gray-500">This may take a moment</p>
    </div>
  );

  const renderCompleteStep = () => {
    if (!result) return null;

    return (
      <div className="space-y-4">
        <div className="text-center py-6">
          {result.success ? (
            <CheckCircle2 className="w-16 h-16 mx-auto text-green-500 mb-4" />
          ) : (
            <XCircle className="w-16 h-16 mx-auto text-red-500 mb-4" />
          )}
          <h3 className="text-xl font-semibold mb-2">
            {result.success ? 'Import Complete' : 'Import Completed with Errors'}
          </h3>
        </div>

        <div className="grid grid-cols-4 gap-2 text-sm">
          <div className="p-3 bg-green-100 rounded text-center">
            <div className="text-2xl font-bold text-green-700">
              {result.importedCount}
            </div>
            <div className="text-green-600">Imported</div>
          </div>
          <div className="p-3 bg-blue-100 rounded text-center">
            <div className="text-2xl font-bold text-blue-700">
              {result.updatedCount}
            </div>
            <div className="text-blue-600">Updated</div>
          </div>
          <div className="p-3 bg-gray-100 rounded text-center">
            <div className="text-2xl font-bold text-gray-700">
              {result.skippedCount}
            </div>
            <div className="text-gray-600">Skipped</div>
          </div>
          <div className="p-3 bg-red-100 rounded text-center">
            <div className="text-2xl font-bold text-red-700">
              {result.failedCount}
            </div>
            <div className="text-red-600">Failed</div>
          </div>
        </div>

        {result.errorMessages.length > 0 && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <h4 className="font-medium text-red-800 mb-2">Errors</h4>
            <ul className="list-disc list-inside text-sm text-red-700">
              {result.errorMessages.map((msg, idx) => (
                <li key={idx}>{msg}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex justify-center pt-4 border-t">
          <Button onClick={handleClose}>
            Done
          </Button>
        </div>
      </div>
    );
  };

  // Quick Template Dialog
  const renderTemplateDialog = () => {
    if (!templateDialogOpen) return null;

    return (
      <div className="fixed inset-0 z-[60] flex items-center justify-center">
        <div
          className="absolute inset-0 bg-black/50"
          onClick={() => setTemplateDialogOpen(false)}
        />
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
          <h3 className="text-lg font-semibold mb-4">
            Create Rotation Template
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Abbreviation
              </label>
              <input
                type="text"
                value={templateAbbrev}
                onChange={(e) => setTemplateAbbrev(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="e.g., Cardiology"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Activity Type
              </label>
              <select
                value={templateType}
                onChange={(e) => setTemplateType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                {ACTIVITY_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="leaveEligible"
                checked={templateLeaveEligible}
                onChange={(e) => setTemplateLeaveEligible(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="leaveEligible" className="text-sm text-gray-700">
                Leave Eligible
              </label>
            </div>
          </div>

          <div className="flex justify-end space-x-2 mt-6">
            <Button
              variant="ghost"
              onClick={() => setTemplateDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateTemplate}
              disabled={!templateAbbrev || !templateName}
            >
              Create Template
            </Button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={handleClose}
        title="Import Block Assignments"
        maxWidth="max-w-2xl"
      >
        {step === 'upload' && renderUploadStep()}
        {step === 'preview' && renderPreviewStep()}
        {step === 'importing' && renderImportingStep()}
        {step === 'complete' && renderCompleteStep()}
      </Modal>

      {renderTemplateDialog()}
    </>
  );
}
