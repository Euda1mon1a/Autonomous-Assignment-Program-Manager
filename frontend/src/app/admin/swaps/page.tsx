'use client';

/**
 * Admin Force Swap Page
 *
 * Administrative interface for handling schedule swap requests.
 * Supports two workflows:
 * 1. Execute Swap: Paired swap between source and target faculty
 * 2. Direct Assignment Edit: Modify individual assignments
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
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { LoadingSpinner } from '@/components/LoadingSpinner';
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

// ============================================================================
// Types
// ============================================================================

type AdminSwapTab = 'execute' | 'direct';

interface AssignmentChange {
  id: string;
  type: 'add' | 'remove';
  assignmentId?: string;
  data?: {
    block_id: string;
    person_id: string;
    role: string;
    activity_override?: string;
  };
  description: string;
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
      <div className="flex items-center gap-2 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
        <Loader2 className="w-4 h-4 animate-spin text-violet-400" />
        <span className="text-slate-300">Validating...</span>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div
      className={`p-4 rounded-lg border ${
        result.valid
          ? 'bg-emerald-500/10 border-emerald-500/30'
          : 'bg-amber-500/10 border-amber-500/30'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        {result.valid ? (
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
        ) : (
          <AlertTriangle className="w-5 h-5 text-amber-400" />
        )}
        <span className="font-medium text-white">
          {result.valid ? 'Validation Passed' : 'Validation Issues'}
        </span>
      </div>
      {result.errors?.map((error, i) => (
        <div key={i} className="flex items-start gap-2 text-sm text-red-400 mt-1">
          <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          {error}
        </div>
      ))}
      {result.warnings?.map((warning, i) => (
        <div key={i} className="flex items-start gap-2 text-sm text-amber-400 mt-1">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          {warning}
        </div>
      ))}
      {result.backToBackConflict && (
        <div className="flex items-start gap-2 text-sm text-amber-400 mt-1">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          Creates back-to-back FMIT blocks
        </div>
      )}
      {result.externalConflict && (
        <div className="flex items-start gap-2 text-sm text-amber-400 mt-1">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
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
      source_faculty_id: sourceFacultyId,
      source_week: sourceWeek,
      target_faculty_id: targetFacultyId,
      target_week: swapType === SwapType.ONE_TO_ONE ? targetWeek : undefined,
      swap_type: swapType,
      reason,
    });
  };

  const handleExecute = () => {
    if (!sourceFacultyId || !targetFacultyId || !sourceWeek) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (swapType === SwapType.ONE_TO_ONE && !targetWeek) {
      toast.error('Target week required for one-to-one swap');
      return;
    }

    executeMutation.mutate(
      {
        source_faculty_id: sourceFacultyId,
        source_week: sourceWeek,
        target_faculty_id: targetFacultyId,
        target_week: swapType === SwapType.ONE_TO_ONE ? targetWeek : undefined,
        swap_type: swapType,
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
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Users className="w-4 h-4" />
            Source Faculty
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-xs text-slate-300 mb-1">Select Faculty</label>
              <select
                value={sourceFacultyId}
                onChange={(e) => setSourceFacultyId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
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
              <label className="block text-xs text-slate-300 mb-1">Week (Block Start)</label>
              <select
                value={sourceWeek}
                onChange={(e) => setSourceWeek(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
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
              <div className="text-xs text-slate-300 bg-slate-800 rounded p-2">
                Selected: <span className="text-white">{sourceFaculty.name}</span>
              </div>
            )}
          </div>
        </div>

        {/* Target Faculty */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Users className="w-4 h-4" />
            Target Faculty
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-xs text-slate-300 mb-1">Select Faculty</label>
              <select
                value={targetFacultyId}
                onChange={(e) => setTargetFacultyId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
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
                <label className="block text-xs text-slate-300 mb-1">Week (Block Start)</label>
                <select
                  value={targetWeek}
                  onChange={(e) => setTargetWeek(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
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
              <div className="text-xs text-slate-300 bg-slate-800 rounded p-2">
                Selected: <span className="text-white">{targetFaculty.name}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Swap Type and Reason */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Swap Type</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={swapType === SwapType.ONE_TO_ONE}
                  onChange={() => setSwapType(SwapType.ONE_TO_ONE)}
                  className="w-4 h-4 text-violet-600 bg-slate-700 border-slate-600 focus:ring-violet-500"
                />
                <span className="text-sm text-slate-300">One-to-One</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={swapType === SwapType.ABSORB}
                  onChange={() => setSwapType(SwapType.ABSORB)}
                  className="w-4 h-4 text-violet-600 bg-slate-700 border-slate-600 focus:ring-violet-500"
                />
                <span className="text-sm text-slate-300">Absorb</span>
              </label>
            </div>
            <p className="text-xs text-slate-300 mt-2">
              {swapType === SwapType.ONE_TO_ONE
                ? 'Both faculty trade their weeks bidirectionally'
                : 'Target absorbs source\'s week (no return assignment)'}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Reason</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter reason for swap..."
              rows={3}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 resize-none"
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
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {validateMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <CheckCircle2 className="w-4 h-4" />
          )}
          Validate (Dry Run)
        </button>

        <button
          onClick={handleExecute}
          disabled={
            !sourceFacultyId ||
            !targetFacultyId ||
            !sourceWeek ||
            (swapType === SwapType.ONE_TO_ONE && !targetWeek) ||
            executeMutation.isPending
          }
          className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {executeMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <ArrowLeftRight className="w-4 h-4" />
          )}
          Execute Swap
        </button>
      </div>
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

  // Get block date range
  const selectedBlockRange = useMemo(() => {
    if (!selectedBlock || !blockRanges) return null;
    return blockRanges.find((b) => b.blockNumber === Number(selectedBlock));
  }, [selectedBlock, blockRanges]);

  // Fetch assignments for selected faculty/block
  const { data: assignmentsData, isLoading: assignmentsLoading } = useAssignments(
    selectedBlockRange
      ? {
          person_id: selectedFacultyId,
          start_date: selectedBlockRange.startDate,
          end_date: selectedBlockRange.endDate,
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

  const handleApplyChanges = async () => {
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
      {/* Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <div>
          <label className="block text-xs text-slate-300 mb-1">Select Faculty</label>
          <select
            value={selectedFacultyId}
            onChange={(e) => {
              setSelectedFacultyId(e.target.value);
              setPendingChanges([]);
            }}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
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
          <label className="block text-xs text-slate-300 mb-1">Select Block</label>
          <select
            value={selectedBlock}
            onChange={(e) => {
              setSelectedBlock(e.target.value);
              setPendingChanges([]);
            }}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
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
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Current Assignments
            </h3>
            <span className="text-xs text-slate-300">
              {assignments.length} assignment(s)
            </span>
          </div>

          {assignmentsLoading ? (
            <div className="flex items-center justify-center h-32">
              <LoadingSpinner />
            </div>
          ) : assignments.length === 0 ? (
            <div className="text-center py-8 text-slate-300">
              No assignments found for this faculty/block combination
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-800">
                  <th className="text-left py-2 px-4 text-slate-300 font-medium">Role</th>
                  <th className="text-left py-2 px-4 text-slate-300 font-medium">Activity</th>
                  <th className="text-left py-2 px-4 text-slate-300 font-medium">Block</th>
                  <th className="w-20 py-2 px-4"></th>
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
                      className={`border-t border-slate-700/50 ${
                        isRemoved ? 'opacity-40 line-through' : ''
                      }`}
                    >
                      <td className="py-2 px-4 text-slate-300">{assignment.role}</td>
                      <td className="py-2 px-4 text-slate-300">
                        {assignment.activityOverride || 'Default'}
                      </td>
                      <td className="py-2 px-4 text-slate-300">{assignment.blockId}</td>
                      <td className="py-2 px-4">
                        {!isRemoved && (
                          <button
                            onClick={() =>
                              handleRemoveAssignment({
                                id: assignment.id,
                                role: assignment.role,
                              })
                            }
                            className="p-1 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded transition-colors"
                            title="Remove assignment"
                          >
                            <Trash2 className="w-4 h-4" />
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
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-amber-400 mb-3 flex items-center gap-2">
            <Pencil className="w-4 h-4" />
            Pending Changes ({pendingChanges.length})
          </h3>

          <div className="space-y-2">
            {pendingChanges.map((change) => (
              <div
                key={change.id}
                className="flex items-center justify-between bg-slate-800/50 rounded px-3 py-2"
              >
                <span className="text-sm text-slate-300">
                  {change.type === 'remove' ? '- ' : '+ '}
                  {change.description}
                </span>
                <button
                  onClick={() => handleUndoChange(change.id)}
                  className="text-xs text-slate-300 hover:text-white transition-colors"
                >
                  Undo
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3 mt-4">
            <button
              onClick={() => setPendingChanges([])}
              className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
            >
              Clear All
            </button>
            <button
              onClick={handleApplyChanges}
              disabled={deleteMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              Apply Changes
            </button>
          </div>
        </div>
      )}
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

  const handleRollback = (swap: SwapRequest) => {
    if (!confirm(`Rollback swap between ${swap.sourceFacultyName} and ${swap.targetFacultyName}?`)) {
      return;
    }

    rollbackMutation.mutate(
      { swap_id: swap.id, reason: 'Admin rollback' },
      {
        onSuccess: () => {
          toast.success('Swap rolled back successfully');
        },
        onError: (error) => {
          toast.error(`Rollback failed: ${error.message}`);
        },
      }
    );
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
        <History className="w-4 h-4" />
        Recent Swaps
      </h3>

      {isLoading ? (
        <div className="flex items-center justify-center h-24">
          <LoadingSpinner />
        </div>
      ) : recentSwaps.length === 0 ? (
        <div className="text-center py-6 text-slate-300 text-sm">
          No recent swaps
        </div>
      ) : (
        <div className="space-y-2">
          {recentSwaps.map((swap) => (
            <div key={swap.id} className="bg-slate-800 rounded-lg p-3 text-xs">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-slate-300">
                    {swap.sourceFacultyName} ↔ {swap.targetFacultyName}
                  </div>
                  <div className="text-slate-300 mt-1">
                    {swap.swapType === SwapType.ONE_TO_ONE ? 'One-to-One' : 'Absorb'}
                    {swap.executedAt && (
                      <> • {format(new Date(swap.executedAt), 'MMM d, h:mm a')}</>
                    )}
                  </div>
                </div>
                {canRollback(swap) && (
                  <button
                    onClick={() => handleRollback(swap)}
                    disabled={rollbackMutation.isPending}
                    className="text-amber-400 hover:text-amber-300 transition-colors"
                    title="Rollback (within 24h)"
                  >
                    <RefreshCw className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          ))}

          {swapHistory && swapHistory.items.length > 5 && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="w-full text-center text-xs text-violet-400 hover:text-violet-300 py-2 flex items-center justify-center gap-1"
            >
              {showAll ? 'Show Less' : `Show All (${swapHistory.items.length})`}
              <ChevronDown className={`w-3 h-3 transition-transform ${showAll ? 'rotate-180' : ''}`} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminSwapsPage() {
  const [activeTab, setActiveTab] = useState<AdminSwapTab>('execute');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
              <ArrowLeftRight className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Force Swap</h1>
              <p className="text-sm text-slate-300">
                Execute schedule changes and direct assignment edits
              </p>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-4">
            <button
              onClick={() => setActiveTab('execute')}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-colors ${
                activeTab === 'execute'
                  ? 'bg-violet-600 text-white'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <ArrowLeftRight className="w-4 h-4" />
              Execute Swap
            </button>
            <button
              onClick={() => setActiveTab('direct')}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-colors ${
                activeTab === 'direct'
                  ? 'bg-violet-600 text-white'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <Pencil className="w-4 h-4" />
              Direct Assignment Edit
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Panel */}
          <div className="lg:col-span-3">
            {activeTab === 'execute' && <ExecuteSwapPanel />}
            {activeTab === 'direct' && <DirectAssignmentPanel />}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <RecentActivitySidebar />
          </div>
        </div>
      </main>
    </div>
  );
}
