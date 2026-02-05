'use client';

/**
 * Block Schedule Import Page (Staging Workflow)
 *
 * Multi-step import workflow:
 * 1. Upload Excel file -> Stage
 * 2. Preview staged vs existing (diff view)
 * 3. Apply or Reject
 * 4. Rollback if needed
 */

import { useState, useCallback } from 'react';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Undo2,
  Eye,
  Trash2,
  ArrowRight,
  Plus,
  Edit3,
  AlertOctagon,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useToast } from '@/contexts/ToastContext';
import {
  useStageImport,
  useImportBatch,
  useImportPreview,
  useApplyImport,
  useRollbackImport,
  useDeleteImportBatch,
} from '@/hooks/useImportStaging';
import { ConflictResolutionMode } from '@/types/import';
import type { StagedAssignmentResponse } from '@/types/import';

// ============================================================================
// Types
// ============================================================================

type WorkflowStep = 'upload' | 'staged' | 'applying' | 'applied';

// ============================================================================
// Helper Components
// ============================================================================

function StatusBadge({
  type,
  count,
}: {
  type: 'new' | 'update' | 'conflict' | 'skip';
  count: number;
}) {
  const configs = {
    new: { icon: Plus, color: 'bg-green-900/50 text-green-300', label: 'New' },
    update: { icon: Edit3, color: 'bg-blue-900/50 text-blue-300', label: 'Update' },
    conflict: { icon: AlertTriangle, color: 'bg-red-900/50 text-red-300', label: 'Conflict' },
    skip: { icon: XCircle, color: 'bg-slate-700/50 text-slate-400', label: 'Skip' },
  };

  const config = configs[type];
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.color}`}>
      <Icon className="w-4 h-4" />
      <span className="font-medium">{count}</span>
      <span className="text-sm opacity-75">{config.label}</span>
    </div>
  );
}

function AssignmentRow({ assignment }: { assignment: StagedAssignmentResponse }) {
  const statusColors = {
    pending: 'bg-slate-700/50',
    approved: 'bg-green-900/30',
    skipped: 'bg-slate-800/50 opacity-50',
    applied: 'bg-green-900/50',
    failed: 'bg-red-900/50',
  };

  const conflictIcons = {
    none: null,
    duplicate: <span title="Duplicate"><AlertTriangle className="w-4 h-4 text-amber-400" /></span>,
    overwrite: <span title="Will overwrite"><Edit3 className="w-4 h-4 text-blue-400" /></span>,
  };

  return (
    <tr className={`${statusColors[assignment.status]} hover:bg-slate-700/30 transition-colors`}>
      <td className="px-4 py-2">
        <div className="flex items-center gap-2">
          {assignment.conflictType && conflictIcons[assignment.conflictType]}
          <span className="text-white">{assignment.personName}</span>
          {assignment.matchedPersonName && assignment.personMatchConfidence && assignment.personMatchConfidence < 100 && (
            <span className="text-xs text-amber-400" title="Fuzzy match">
              ~{assignment.personMatchConfidence}%
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-2 text-slate-300">{assignment.assignmentDate}</td>
      <td className="px-4 py-2 text-slate-300">{assignment.slot || 'Full Day'}</td>
      <td className="px-4 py-2">
        <span className="text-white">{assignment.rotationName || '-'}</span>
        {assignment.matchedRotationName && assignment.rotationMatchConfidence && assignment.rotationMatchConfidence < 100 && (
          <span className="text-xs text-amber-400 ml-2" title="Fuzzy match">
            ~{assignment.rotationMatchConfidence}%
          </span>
        )}
      </td>
      <td className="px-4 py-2">
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${
          assignment.status === 'approved' ? 'bg-green-900/50 text-green-300' :
          assignment.status === 'skipped' ? 'bg-slate-600 text-slate-400' :
          assignment.status === 'failed' ? 'bg-red-900/50 text-red-300' :
          'bg-slate-600 text-slate-300'
        }`}>
          {assignment.status}
        </span>
      </td>
    </tr>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function BlockImportPage() {
  const { toast } = useToast();

  // Workflow state
  const [step, setStep] = useState<WorkflowStep>('upload');
  const [batchId, setBatchId] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [conflictResolution, setConflictResolution] = useState<ConflictResolutionMode>(ConflictResolutionMode.UPSERT);
  const [targetBlock, setTargetBlock] = useState<number | undefined>();

  // Queries
  const { data: batch, isLoading: batchLoading } = useImportBatch(batchId);
  const { data: preview, isLoading: previewLoading, refetch: refetchPreview } = useImportPreview(batchId);

  // Mutations
  const stageImport = useStageImport();
  const applyImport = useApplyImport();
  const rollbackImport = useRollbackImport();
  const deleteImport = useDeleteImportBatch();

  // Handlers
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setBatchId(null);
      setStep('upload');
    }
  }, []);

  const handleStage = useCallback(async () => {
    if (!file) return;

    try {
      const result = await stageImport.mutateAsync({
        file,
        targetBlock,
        conflictResolution,
      });
      setBatchId(result.batchId);
      setStep('staged');
      toast.success('File staged successfully. Review the preview below.');
    } catch (error) {
      toast.error(`Staging failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [file, targetBlock, conflictResolution, stageImport, toast]);

  const handleApply = useCallback(async () => {
    if (!batchId) return;

    setStep('applying');
    try {
      const result = await applyImport.mutateAsync({
        batchId,
        validateAcgme: true,
      });
      setStep('applied');
      toast.success(`Applied ${result.appliedCount} assignments successfully.`);
    } catch (error) {
      setStep('staged');
      toast.error(`Apply failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [batchId, applyImport, toast]);

  const handleRollback = useCallback(async () => {
    if (!batchId) return;

    try {
      const result = await rollbackImport.mutateAsync({ batchId });
      toast.success(`Rolled back ${result.rolledBackCount} assignments.`);
      setStep('staged');
      refetchPreview();
    } catch (error) {
      toast.error(`Rollback failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [batchId, rollbackImport, refetchPreview, toast]);

  const handleReject = useCallback(async () => {
    if (!batchId) return;

    try {
      await deleteImport.mutateAsync(batchId);
      toast.info('Import batch rejected and deleted.');
      setBatchId(null);
      setFile(null);
      setStep('upload');
    } catch (error) {
      toast.error(`Delete failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [batchId, deleteImport, toast]);

  const handleReset = useCallback(() => {
    setBatchId(null);
    setFile(null);
    setStep('upload');
  }, []);

  const isLoading = stageImport.isPending || batchLoading || previewLoading;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-lg">
                <FileSpreadsheet className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Block Schedule Import</h1>
                <p className="text-sm text-slate-300">
                  Upload Excel, preview changes, then apply
                </p>
              </div>
            </div>

            {batchId && (
              <Button
                onClick={handleReset}
                variant="outline"
                className="border-slate-600 text-slate-300"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                New Import
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Step 1: Upload */}
        {step === 'upload' && (
          <Card className="p-6 bg-slate-800/50 border-slate-700">
            <h2 className="text-lg font-semibold text-white mb-4">
              <Upload className="w-5 h-5 inline mr-2" />
              Upload Excel File
            </h2>

            <div className="space-y-4">
              {/* File Input */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Select File (.xlsx, .xls)
                </label>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-slate-300
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-md file:border-0
                    file:text-sm file:font-semibold
                    file:bg-blue-600 file:text-white
                    hover:file:bg-blue-500
                    cursor-pointer"
                />
                {file && (
                  <p className="mt-2 text-sm text-slate-400">
                    <FileSpreadsheet className="w-4 h-4 inline mr-1" />
                    {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </p>
                )}
              </div>

              {/* Options */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Target Block (optional)
                  </label>
                  <select
                    value={targetBlock || ''}
                    onChange={(e) => setTargetBlock(e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
                  >
                    <option value="">Auto-detect</option>
                    {Array.from({ length: 26 }, (_, i) => i + 1).map((b) => (
                      <option key={b} value={b}>Block {b}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Conflict Resolution
                  </label>
                  <select
                    value={conflictResolution}
                    onChange={(e) => setConflictResolution(e.target.value as ConflictResolutionMode)}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
                  >
                    <option value="upsert">Upsert (create or update)</option>
                    <option value="replace">Replace (overwrite all)</option>
                    <option value="merge">Merge (skip duplicates)</option>
                  </select>
                </div>
              </div>

              {/* Stage Button */}
              <Button
                onClick={handleStage}
                disabled={!file || stageImport.isPending}
                className="bg-blue-600 hover:bg-blue-500"
              >
                {stageImport.isPending ? (
                  <>
                    <LoadingSpinner size="sm" />
                    Staging...
                  </>
                ) : (
                  <>
                    <Eye className="w-4 h-4 mr-2" />
                    Stage & Preview
                  </>
                )}
              </Button>
            </div>
          </Card>
        )}

        {/* Step 2: Preview */}
        {(step === 'staged' || step === 'applying') && preview && (
          <>
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatusBadge type="new" count={preview.newCount} />
              <StatusBadge type="update" count={preview.updateCount} />
              <StatusBadge type="conflict" count={preview.conflictCount} />
              <StatusBadge type="skip" count={preview.skipCount} />
            </div>

            {/* ACGME Violations Warning */}
            {preview.acgmeViolations.length > 0 && (
              <Alert variant="warning">
                <AlertOctagon className="w-5 h-5 inline mr-2" />
                <span className="font-medium">ACGME Violations Detected:</span>
                <ul className="list-disc list-inside mt-2 text-sm">
                  {preview.acgmeViolations.map((v, i) => (
                    <li key={i}>{v}</li>
                  ))}
                </ul>
              </Alert>
            )}

            {/* Staged Assignments Table */}
            <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
              <div className="p-4 border-b border-slate-700">
                <h3 className="text-lg font-semibold text-white">
                  Staged Assignments ({preview.totalStaged})
                </h3>
              </div>

              <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-900/50 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">
                        Person
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">
                        Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">
                        Slot
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">
                        Rotation
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-300 uppercase">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/50">
                    {preview.stagedAssignments.map((assignment) => (
                      <AssignmentRow key={assignment.id} assignment={assignment} />
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Action Buttons */}
            <div className="flex items-center gap-4">
              <Button
                onClick={handleApply}
                disabled={step === 'applying' || applyImport.isPending}
                className="bg-green-600 hover:bg-green-500"
              >
                {applyImport.isPending ? (
                  <>
                    <LoadingSpinner size="sm" />
                    Applying...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Apply Import
                  </>
                )}
              </Button>

              <Button
                onClick={handleReject}
                disabled={step === 'applying' || deleteImport.isPending}
                variant="outline"
                className="border-red-600 text-red-400 hover:bg-red-900/20"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Reject
              </Button>
            </div>
          </>
        )}

        {/* Step 3: Applied */}
        {step === 'applied' && batch && (
          <Card className="p-6 bg-slate-800/50 border-slate-700">
            <Alert variant="success" className="mb-6">
              <CheckCircle2 className="w-5 h-5 inline mr-2" />
              Import applied successfully!
            </Alert>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-slate-700/50 rounded-lg">
                <div className="text-2xl font-bold text-green-400">
                  {batch.counts.applied}
                </div>
                <div className="text-sm text-slate-400">Applied</div>
              </div>
              <div className="p-4 bg-slate-700/50 rounded-lg">
                <div className="text-2xl font-bold text-slate-400">
                  {batch.counts.skipped}
                </div>
                <div className="text-sm text-slate-400">Skipped</div>
              </div>
              <div className="p-4 bg-slate-700/50 rounded-lg">
                <div className="text-2xl font-bold text-red-400">
                  {batch.counts.failed}
                </div>
                <div className="text-sm text-slate-400">Failed</div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {batch.rollbackAvailable && (
                <Button
                  onClick={handleRollback}
                  disabled={rollbackImport.isPending}
                  variant="outline"
                  className="border-amber-600 text-amber-400 hover:bg-amber-900/20"
                >
                  <Undo2 className="w-4 h-4 mr-2" />
                  {rollbackImport.isPending ? 'Rolling back...' : 'Rollback'}
                </Button>
              )}

              <Button
                onClick={handleReset}
                className="bg-blue-600 hover:bg-blue-500"
              >
                <ArrowRight className="w-4 h-4 mr-2" />
                New Import
              </Button>
            </div>
          </Card>
        )}

        {/* Loading State */}
        {isLoading && step !== 'upload' && (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        )}
      </main>
    </div>
  );
}
