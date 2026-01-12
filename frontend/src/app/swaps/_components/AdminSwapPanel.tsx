'use client';

/**
 * AdminSwapPanel Component
 *
 * Administrative interface for schedule swap operations.
 * Supports two workflows:
 * 1. Execute Swap: Paired swap between source and target faculty (Tier 1+)
 * 2. Direct Assignment Edit: Modify individual assignments (Tier 2 only)
 *
 * @see docs/reviews/2026-01-11-frontend-consolidation-map.md
 */

import { useState, useMemo } from 'react';
import {
  ArrowLeftRight,
  RefreshCw,
  Users,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  Pencil,
  Trash2,
  History,
  ChevronDown,
  ShieldAlert,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { useToast } from '@/contexts/ToastContext';
import { useFaculty } from '@/hooks/usePeople';
import { useBlockRanges } from '@/lib/hooks';
import {
  useExecuteSwap,
  useValidateSwap,
  useRollbackSwap,
  useSwapList,
  SwapType,
  SwapStatus,
  type SwapValidationResult,
  type SwapRequest,
} from '@/hooks/useSwaps';
import {
  useAssignments,
  useDeleteAssignment,
} from '@/hooks/useSchedule';
import type { RiskTier } from '@/components/ui/RiskBar';

// ============================================================================
// Types
// ============================================================================

type AdminSwapTab = 'execute' | 'direct';

interface AssignmentChange {
  id: string;
  type: 'add' | 'remove';
  assignmentId?: string;
  data?: {
    blockId: string;
    personId: string;
    role: string;
    activityOverride?: string;
  };
  description: string;
}

interface AdminSwapPanelProps {
  /** User's permission tier (1 = coordinator, 2 = admin) */
  userTier: RiskTier;
}

// ============================================================================
// Validation Warnings Component
// ============================================================================

function ValidationWarnings({
  result,
  isValidating,
}: {
  result: SwapValidationResult | null;
  isValidating: boolean;
}) {
  if (isValidating) {
    return (
      <div className="flex items-center gap-2 p-4 bg-gray-100 rounded-lg border border-gray-200">
        <Loader2 className="w-4 h-4 animate-spin text-blue-600" aria-hidden="true" />
        <span className="text-gray-700">Validating...</span>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div
      className={`p-4 rounded-lg border ${
        result.valid
          ? 'bg-green-50 border-green-200'
          : 'bg-amber-50 border-amber-200'
      }`}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-2 mb-2">
        {result.valid ? (
          <CheckCircle2 className="w-5 h-5 text-green-600" aria-hidden="true" />
        ) : (
          <AlertTriangle className="w-5 h-5 text-amber-600" aria-hidden="true" />
        )}
        <span className="font-medium text-gray-900">
          {result.valid ? 'Validation Passed' : 'Validation Issues'}
        </span>
      </div>
      {result.errors?.map((error, i) => (
        <div key={i} className="flex items-start gap-2 text-sm text-red-700 mt-1">
          <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
          {error}
        </div>
      ))}
      {result.warnings?.map((warning, i) => (
        <div key={i} className="flex items-start gap-2 text-sm text-amber-700 mt-1">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
          {warning}
        </div>
      ))}
      {result.backToBackConflict && (
        <div className="flex items-start gap-2 text-sm text-amber-700 mt-1">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
          Creates back-to-back FMIT blocks
        </div>
      )}
      {result.externalConflict && (
        <div className="flex items-start gap-2 text-sm text-amber-700 mt-1">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
          External conflict: {result.externalConflict}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Execute Swap Panel
// ============================================================================

function ExecuteSwapPanel() {
  const { toast } = useToast();

  // Faculty data
  const { data: facultyData, isLoading: facultyLoading } = useFaculty();
  const { data: blockRanges } = useBlockRanges();

  // Form state
  const [sourceFacultyId, setSourceFacultyId] = useState('');
  const [targetFacultyId, setTargetFacultyId] = useState('');
  const [sourceWeek, setSourceWeek] = useState('');
  const [targetWeek, setTargetWeek] = useState('');
  const [swapType, setSwapType] = useState<SwapType>(SwapType.ONE_TO_ONE);
  const [reason, setReason] = useState('');

  // Confirmation dialog state
  const [showConfirm, setShowConfirm] = useState(false);

  // Mutations
  const validateMutation = useValidateSwap();
  const executeMutation = useExecuteSwap();

  // Derived state
  const faculty = facultyData?.items ?? [];
  const sourceFaculty = faculty.find((f) => f.id === sourceFacultyId);
  const targetFaculty = faculty.find((f) => f.id === targetFacultyId);

  const handleValidate = () => {
    if (!sourceFacultyId || !targetFacultyId || !sourceWeek) {
      toast.error('Please fill in all required fields');
      return;
    }

    validateMutation.mutate({
      sourceFacultyId: sourceFacultyId,
      sourceWeek: sourceWeek,
      targetFacultyId: targetFacultyId,
      targetWeek: swapType === SwapType.ONE_TO_ONE ? targetWeek : undefined,
      swapType: swapType,
      reason,
    });
  };

  const handleExecuteClick = () => {
    if (!sourceFacultyId || !targetFacultyId || !sourceWeek) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (swapType === SwapType.ONE_TO_ONE && !targetWeek) {
      toast.error('Target week required for one-to-one swap');
      return;
    }

    setShowConfirm(true);
  };

  const handleExecuteConfirm = () => {
    executeMutation.mutate(
      {
        sourceFacultyId: sourceFacultyId,
        sourceWeek: sourceWeek,
        targetFacultyId: targetFacultyId,
        targetWeek: swapType === SwapType.ONE_TO_ONE ? targetWeek : undefined,
        swapType: swapType,
        reason,
      },
      {
        onSuccess: (result) => {
          if (result.success) {
            toast.success(`Swap executed successfully (ID: ${result.swapId})`);
            // Reset form
            setSourceFacultyId('');
            setTargetFacultyId('');
            setSourceWeek('');
            setTargetWeek('');
            setReason('');
            validateMutation.reset();
          } else {
            toast.error(result.message || 'Swap execution failed');
          }
        },
        onError: (error) => {
          toast.error(`Swap failed: ${error.message}`);
        },
      }
    );
    setShowConfirm(false);
  };

  if (facultyLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Source and Target Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Source Faculty */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <Users className="w-4 h-4" aria-hidden="true" />
            Source Faculty
          </h3>

          <div className="space-y-4">
            <div>
              <label htmlFor="source-faculty" className="block text-xs text-gray-600 mb-1">
                Select Faculty
              </label>
              <select
                id="source-faculty"
                value={sourceFacultyId}
                onChange={(e) => setSourceFacultyId(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select faculty...</option>
                {faculty.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="source-week" className="block text-xs text-gray-600 mb-1">
                Week (Block Start)
              </label>
              <select
                id="source-week"
                value={sourceWeek}
                onChange={(e) => setSourceWeek(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select week...</option>
                {blockRanges?.map((block) => (
                  <option key={block.blockNumber} value={block.startDate}>
                    Block {block.blockNumber}: {format(parseISO(block.startDate), 'MMM d')} -{' '}
                    {format(parseISO(block.endDate), 'MMM d')}
                  </option>
                ))}
              </select>
            </div>

            {sourceFaculty && (
              <div className="text-xs text-gray-600 bg-gray-50 rounded p-2">
                Selected: <span className="font-medium text-gray-900">{sourceFaculty.name}</span>
              </div>
            )}
          </div>
        </div>

        {/* Target Faculty */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <Users className="w-4 h-4" aria-hidden="true" />
            Target Faculty
          </h3>

          <div className="space-y-4">
            <div>
              <label htmlFor="target-faculty" className="block text-xs text-gray-600 mb-1">
                Select Faculty
              </label>
              <select
                id="target-faculty"
                value={targetFacultyId}
                onChange={(e) => setTargetFacultyId(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select faculty...</option>
                {faculty
                  .filter((f) => f.id !== sourceFacultyId)
                  .map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
              </select>
            </div>

            {swapType === SwapType.ONE_TO_ONE && (
              <div>
                <label htmlFor="target-week" className="block text-xs text-gray-600 mb-1">
                  Week (Block Start)
                </label>
                <select
                  id="target-week"
                  value={targetWeek}
                  onChange={(e) => setTargetWeek(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select week...</option>
                  {blockRanges?.map((block) => (
                    <option key={block.blockNumber} value={block.startDate}>
                      Block {block.blockNumber}: {format(parseISO(block.startDate), 'MMM d')} -{' '}
                      {format(parseISO(block.endDate), 'MMM d')}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {targetFaculty && (
              <div className="text-xs text-gray-600 bg-gray-50 rounded p-2">
                Selected: <span className="font-medium text-gray-900">{targetFaculty.name}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Swap Type and Reason */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <fieldset>
              <legend className="block text-sm font-medium text-gray-700 mb-2">Swap Type</legend>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={swapType === SwapType.ONE_TO_ONE}
                    onChange={() => setSwapType(SwapType.ONE_TO_ONE)}
                    className="w-4 h-4 text-blue-600 bg-white border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">One-to-One</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={swapType === SwapType.ABSORB}
                    onChange={() => setSwapType(SwapType.ABSORB)}
                    className="w-4 h-4 text-blue-600 bg-white border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Absorb</span>
                </label>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {swapType === SwapType.ONE_TO_ONE
                  ? 'Both faculty trade their weeks bidirectionally'
                  : "Target absorbs source's week (no return assignment)"}
              </p>
            </fieldset>
          </div>

          <div>
            <label htmlFor="swap-reason" className="block text-sm font-medium text-gray-700 mb-2">
              Reason
            </label>
            <textarea
              id="swap-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter reason for swap..."
              rows={3}
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
        </div>
      </div>

      {/* Validation Results */}
      <ValidationWarnings
        result={validateMutation.data ?? null}
        isValidating={validateMutation.isPending}
      />

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={handleValidate}
          disabled={!sourceFacultyId || !targetFacultyId || !sourceWeek || validateMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {validateMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
          ) : (
            <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
          )}
          Validate (Dry Run)
        </button>

        <button
          onClick={handleExecuteClick}
          disabled={
            !sourceFacultyId ||
            !targetFacultyId ||
            !sourceWeek ||
            (swapType === SwapType.ONE_TO_ONE && !targetWeek) ||
            executeMutation.isPending
          }
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {executeMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
          ) : (
            <ArrowLeftRight className="w-4 h-4" aria-hidden="true" />
          )}
          Execute Swap
        </button>
      </div>

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleExecuteConfirm}
        title="Confirm Swap Execution"
        message={`Are you sure you want to execute this swap between ${sourceFaculty?.name || 'source'} and ${targetFaculty?.name || 'target'}? This will modify their schedule assignments.`}
        confirmLabel="Execute Swap"
        variant="warning"
        isLoading={executeMutation.isPending}
      />
    </div>
  );
}

// ============================================================================
// Direct Assignment Panel
// ============================================================================

function DirectAssignmentPanel() {
  const { toast } = useToast();

  // Faculty and block data
  const { data: facultyData, isLoading: facultyLoading } = useFaculty();
  const { data: blockRanges } = useBlockRanges();

  // Selection state
  const [selectedFacultyId, setSelectedFacultyId] = useState('');
  const [selectedBlock, setSelectedBlock] = useState('');

  // Confirmation dialog state
  const [showConfirm, setShowConfirm] = useState(false);
  const [confirmMessage, setConfirmMessage] = useState('');

  // Get block date range
  const selectedBlockRange = useMemo(() => {
    if (!selectedBlock || !blockRanges) return null;
    return blockRanges.find((b) => b.blockNumber === Number(selectedBlock));
  }, [selectedBlock, blockRanges]);

  // Fetch assignments for selected faculty/block
  const { data: assignmentsData, isLoading: assignmentsLoading } = useAssignments(
    selectedBlockRange
      ? {
          personId: selectedFacultyId,
          startDate: selectedBlockRange.startDate,
          endDate: selectedBlockRange.endDate,
        }
      : undefined,
    {
      enabled: !!selectedFacultyId && !!selectedBlockRange,
    }
  );

  // Mutations
  const deleteMutation = useDeleteAssignment();

  // Pending changes (local staging area)
  const [pendingChanges, setPendingChanges] = useState<AssignmentChange[]>([]);

  const faculty = facultyData?.items ?? [];
  const assignments = assignmentsData?.items ?? [];

  const handleRemoveAssignment = (assignment: { id: string; role: string }) => {
    // Check if already in pending changes
    if (pendingChanges.some((c) => c.assignmentId === assignment.id && c.type === 'remove')) {
      return;
    }

    setPendingChanges((prev) => [
      ...prev,
      {
        id: `remove-${assignment.id}`,
        type: 'remove',
        assignmentId: assignment.id,
        description: `Remove ${assignment.role} assignment`,
      },
    ]);
  };

  const handleUndoChange = (changeId: string) => {
    setPendingChanges((prev) => prev.filter((c) => c.id !== changeId));
  };

  const handleApplyClick = () => {
    if (pendingChanges.length === 0) return;

    const removeCount = pendingChanges.filter((c) => c.type === 'remove').length;
    setConfirmMessage(
      `You are about to apply ${removeCount} assignment deletion(s). This action may not be fully reversible. Are you sure you want to proceed?`
    );
    setShowConfirm(true);
  };

  const handleApplyConfirm = async () => {
    if (pendingChanges.length === 0) return;

    let successCount = 0;
    let errorCount = 0;

    for (const change of pendingChanges) {
      try {
        if (change.type === 'remove' && change.assignmentId) {
          await deleteMutation.mutateAsync(change.assignmentId);
          successCount++;
        }
      } catch {
        errorCount++;
      }
    }

    if (successCount > 0) {
      toast.success(`${successCount} change(s) applied successfully`);
    }
    if (errorCount > 0) {
      toast.error(`${errorCount} change(s) failed`);
    }

    setPendingChanges([]);
    setShowConfirm(false);
  };

  if (facultyLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Warning Banner */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <h3 className="text-sm font-semibold text-red-800">High Impact Operations</h3>
          <p className="text-sm text-red-700 mt-1">
            Direct assignment edits bypass the normal swap workflow and may not be reversible.
            Use with caution and verify all changes before applying.
          </p>
        </div>
      </div>

      {/* Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <div>
          <label htmlFor="direct-faculty" className="block text-xs text-gray-600 mb-1">
            Select Faculty
          </label>
          <select
            id="direct-faculty"
            value={selectedFacultyId}
            onChange={(e) => {
              setSelectedFacultyId(e.target.value);
              setPendingChanges([]);
            }}
            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select faculty...</option>
            {faculty.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="direct-block" className="block text-xs text-gray-600 mb-1">
            Select Block
          </label>
          <select
            id="direct-block"
            value={selectedBlock}
            onChange={(e) => {
              setSelectedBlock(e.target.value);
              setPendingChanges([]);
            }}
            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select block...</option>
            {blockRanges?.map((block) => (
              <option key={block.blockNumber} value={block.blockNumber}>
                Block {block.blockNumber}: {format(parseISO(block.startDate), 'MMM d')} -{' '}
                {format(parseISO(block.endDate), 'MMM d')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Current Assignments */}
      {selectedFacultyId && selectedBlock && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Calendar className="w-4 h-4" aria-hidden="true" />
              Current Assignments
            </h3>
            <span className="text-xs text-gray-500">
              {assignments.length} assignment(s)
            </span>
          </div>

          {assignmentsLoading ? (
            <div className="flex items-center justify-center h-32">
              <LoadingSpinner />
            </div>
          ) : assignments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No assignments found for this faculty/block combination
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left py-2 px-4 text-gray-600 font-medium">Role</th>
                  <th className="text-left py-2 px-4 text-gray-600 font-medium">Activity</th>
                  <th className="text-left py-2 px-4 text-gray-600 font-medium">Block</th>
                  <th className="w-20 py-2 px-4">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((assignment) => {
                  const isRemoved = pendingChanges.some(
                    (c) => c.assignmentId === assignment.id && c.type === 'remove'
                  );

                  return (
                    <tr
                      key={assignment.id}
                      className={`border-t border-gray-100 ${
                        isRemoved ? 'opacity-40 line-through bg-red-50' : ''
                      }`}
                    >
                      <td className="py-2 px-4 text-gray-700">{assignment.role}</td>
                      <td className="py-2 px-4 text-gray-700">
                        {assignment.activityOverride || 'Default'}
                      </td>
                      <td className="py-2 px-4 text-gray-700">{assignment.blockId}</td>
                      <td className="py-2 px-4">
                        {!isRemoved && (
                          <button
                            onClick={() =>
                              handleRemoveAssignment({
                                id: assignment.id,
                                role: assignment.role,
                              })
                            }
                            className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                            title="Remove assignment"
                            aria-label={`Remove ${assignment.role} assignment`}
                          >
                            <Trash2 className="w-4 h-4" aria-hidden="true" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Pending Changes */}
      {pendingChanges.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-amber-800 mb-3 flex items-center gap-2">
            <Pencil className="w-4 h-4" aria-hidden="true" />
            Pending Changes ({pendingChanges.length})
          </h3>

          <div className="space-y-2">
            {pendingChanges.map((change) => (
              <div
                key={change.id}
                className="flex items-center justify-between bg-white rounded px-3 py-2 border border-amber-100"
              >
                <span className="text-sm text-gray-700">
                  {change.type === 'remove' ? '- ' : '+ '}
                  {change.description}
                </span>
                <button
                  onClick={() => handleUndoChange(change.id)}
                  className="text-xs text-gray-500 hover:text-gray-700 transition-colors"
                >
                  Undo
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3 mt-4">
            <button
              onClick={() => setPendingChanges([])}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Clear All
            </button>
            <button
              onClick={handleApplyClick}
              disabled={deleteMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
              ) : (
                <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
              )}
              Apply Changes
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleApplyConfirm}
        title="Confirm Direct Assignment Changes"
        message={confirmMessage}
        confirmLabel="Apply Changes"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

// ============================================================================
// Recent Activity Sidebar
// ============================================================================

function RecentActivitySidebar() {
  const { toast } = useToast();
  const [showAll, setShowAll] = useState(false);

  const { data: swapHistory, isLoading } = useSwapList(
    { status: [SwapStatus.EXECUTED] },
    { staleTime: 30 * 1000 }
  );

  const rollbackMutation = useRollbackSwap();

  const recentSwaps = useMemo(() => {
    if (!swapHistory?.items) return [];
    return swapHistory.items.slice(0, showAll ? 20 : 5);
  }, [swapHistory, showAll]);

  const canRollback = (swap: SwapRequest) => {
    if (!swap.executedAt) return false;
    const hoursAgo =
      (Date.now() - new Date(swap.executedAt).getTime()) / (1000 * 60 * 60);
    return hoursAgo < 24;
  };

  // Confirmation dialog state
  const [showRollbackConfirm, setShowRollbackConfirm] = useState(false);
  const [swapToRollback, setSwapToRollback] = useState<SwapRequest | null>(null);

  const handleRollbackClick = (swap: SwapRequest) => {
    setSwapToRollback(swap);
    setShowRollbackConfirm(true);
  };

  const handleRollbackConfirm = () => {
    if (!swapToRollback) return;

    rollbackMutation.mutate(
      { swapId: swapToRollback.id, reason: 'Admin rollback' },
      {
        onSuccess: () => {
          toast.success('Swap rolled back successfully');
        },
        onError: (error) => {
          toast.error(`Rollback failed: ${error.message}`);
        },
      }
    );
    setShowRollbackConfirm(false);
    setSwapToRollback(null);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <History className="w-4 h-4" aria-hidden="true" />
        Recent Swaps
      </h3>

      {isLoading ? (
        <div className="flex items-center justify-center h-24">
          <LoadingSpinner />
        </div>
      ) : recentSwaps.length === 0 ? (
        <div className="text-center py-6 text-gray-500 text-sm">
          No recent swaps
        </div>
      ) : (
        <div className="space-y-2">
          {recentSwaps.map((swap) => (
            <div key={swap.id} className="bg-gray-50 rounded-lg p-3 text-xs border border-gray-100">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-gray-700 font-medium">
                    {swap.sourceFacultyName} ↔ {swap.targetFacultyName}
                  </div>
                  <div className="text-gray-500 mt-1">
                    {swap.swapType === SwapType.ONE_TO_ONE ? 'One-to-One' : 'Absorb'}
                    {swap.executedAt && (
                      <> • {format(new Date(swap.executedAt), 'MMM d, h:mm a')}</>
                    )}
                  </div>
                </div>
                {canRollback(swap) && (
                  <button
                    onClick={() => handleRollbackClick(swap)}
                    disabled={rollbackMutation.isPending}
                    className="text-amber-600 hover:text-amber-700 transition-colors p-1 hover:bg-amber-50 rounded"
                    title="Rollback (within 24h)"
                    aria-label={`Rollback swap between ${swap.sourceFacultyName} and ${swap.targetFacultyName}`}
                  >
                    <RefreshCw className="w-3 h-3" aria-hidden="true" />
                  </button>
                )}
              </div>
            </div>
          ))}

          {swapHistory && swapHistory.items.length > 5 && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="w-full text-center text-xs text-blue-600 hover:text-blue-700 py-2 flex items-center justify-center gap-1 transition-colors"
            >
              {showAll ? 'Show Less' : `Show All (${swapHistory.items.length})`}
              <ChevronDown
                className={`w-3 h-3 transition-transform ${showAll ? 'rotate-180' : ''}`}
                aria-hidden="true"
              />
            </button>
          )}
        </div>
      )}

      {/* Rollback Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showRollbackConfirm}
        onClose={() => {
          setShowRollbackConfirm(false);
          setSwapToRollback(null);
        }}
        onConfirm={handleRollbackConfirm}
        title="Confirm Swap Rollback"
        message={`Are you sure you want to rollback the swap between ${swapToRollback?.sourceFacultyName} and ${swapToRollback?.targetFacultyName}? This will restore the original schedule assignments.`}
        confirmLabel="Rollback Swap"
        variant="warning"
        isLoading={rollbackMutation.isPending}
      />
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function AdminSwapPanel({ userTier }: AdminSwapPanelProps) {
  const [activeTab, setActiveTab] = useState<AdminSwapTab>('execute');

  // Direct edit tab is only available for Tier 2 (admin) users
  const canAccessDirectEdit = userTier >= 2;

  return (
    <div className="space-y-6">
      {/* Sub-tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4" aria-label="Admin swap actions">
          <button
            onClick={() => setActiveTab('execute')}
            className={`
              flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-sm transition-colors
              ${
                activeTab === 'execute'
                  ? 'border-amber-500 text-amber-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
            role="tab"
            aria-selected={activeTab === 'execute'}
          >
            <ArrowLeftRight className="w-4 h-4" aria-hidden="true" />
            Execute Swap
          </button>
          {canAccessDirectEdit && (
            <button
              onClick={() => setActiveTab('direct')}
              className={`
                flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === 'direct'
                    ? 'border-red-500 text-red-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              role="tab"
              aria-selected={activeTab === 'direct'}
            >
              <Pencil className="w-4 h-4" aria-hidden="true" />
              Direct Assignment Edit
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-red-100 text-red-700 rounded">
                Admin
              </span>
            </button>
          )}
        </nav>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Panel */}
        <div className="lg:col-span-3">
          {activeTab === 'execute' && <ExecuteSwapPanel />}
          {activeTab === 'direct' && canAccessDirectEdit && <DirectAssignmentPanel />}
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <RecentActivitySidebar />
        </div>
      </div>
    </div>
  );
}
