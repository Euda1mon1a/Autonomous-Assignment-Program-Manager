'use client';

/**
 * BulkProgressModal Component
 *
 * Displays progress during batch operations with live updates,
 * individual item status, and cancel functionality.
 */
import React, { useMemo } from 'react';
import {
  X,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
} from 'lucide-react';
import type { BatchOperationResult } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export type BulkOperationType =
  | 'delete'
  | 'update'
  | 'create'
  | 'archive'
  | 'restore'
  | 'duplicate';

export interface BulkProgressItem {
  id: string;
  label: string;
  status: 'pending' | 'processing' | 'success' | 'error';
  error?: string;
}

export interface BulkProgressModalProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Operation type being performed */
  operationType: BulkOperationType;
  /** Total number of items */
  totalItems: number;
  /** Number of completed items */
  completedItems: number;
  /** Number of failed items */
  failedItems: number;
  /** Individual item progress (optional) */
  items?: BulkProgressItem[];
  /** Callback to close modal */
  onClose: () => void;
  /** Callback to cancel operation (optional) */
  onCancel?: () => void;
  /** Whether operation is complete */
  isComplete?: boolean;
  /** Whether cancel is in progress */
  isCancelling?: boolean;
  /** Results from batch operation */
  results?: BatchOperationResult[];
}

// ============================================================================
// Constants
// ============================================================================

const OPERATION_LABELS: Record<BulkOperationType, { title: string; verb: string; pastTense: string }> = {
  delete: { title: 'Deleting Templates', verb: 'Deleting', pastTense: 'deleted' },
  update: { title: 'Updating Templates', verb: 'Updating', pastTense: 'updated' },
  create: { title: 'Creating Templates', verb: 'Creating', pastTense: 'created' },
  archive: { title: 'Archiving Templates', verb: 'Archiving', pastTense: 'archived' },
  restore: { title: 'Restoring Templates', verb: 'Restoring', pastTense: 'restored' },
  duplicate: { title: 'Duplicating Templates', verb: 'Duplicating', pastTense: 'duplicated' },
};

// ============================================================================
// Subcomponents
// ============================================================================

interface ProgressBarProps {
  value: number;
  max: number;
  color?: 'violet' | 'emerald' | 'red';
}

function ProgressBar({ value, max, color = 'violet' }: ProgressBarProps) {
  const percentage = max > 0 ? Math.round((value / max) * 100) : 0;

  const colorClasses = {
    violet: 'bg-violet-500',
    emerald: 'bg-emerald-500',
    red: 'bg-red-500',
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-slate-400">
          {value} of {max}
        </span>
        <span className="text-sm font-medium text-white">{percentage}%</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} transition-all duration-300 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

interface ItemStatusIconProps {
  status: BulkProgressItem['status'];
}

function ItemStatusIcon({ status }: ItemStatusIconProps) {
  switch (status) {
    case 'pending':
      return <Clock className="w-4 h-4 text-slate-500" />;
    case 'processing':
      return <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />;
    case 'success':
      return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
    case 'error':
      return <XCircle className="w-4 h-4 text-red-400" />;
  }
}

// ============================================================================
// Main Component
// ============================================================================

export function BulkProgressModal({
  isOpen,
  operationType,
  totalItems,
  completedItems,
  failedItems,
  items,
  onClose,
  onCancel,
  isComplete = false,
  isCancelling = false,
  results,
}: BulkProgressModalProps) {
  const labels = OPERATION_LABELS[operationType];
  const successCount = completedItems - failedItems;

  // Calculate overall status
  const overallStatus = useMemo(() => {
    if (!isComplete) return 'processing';
    if (failedItems === 0) return 'success';
    if (successCount === 0) return 'error';
    return 'partial';
  }, [isComplete, failedItems, successCount]);

  // Determine header icon and color
  const headerConfig = useMemo(() => {
    switch (overallStatus) {
      case 'processing':
        return {
          icon: <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />,
          bgColor: 'bg-violet-500/20',
        };
      case 'success':
        return {
          icon: <CheckCircle2 className="w-6 h-6 text-emerald-400" />,
          bgColor: 'bg-emerald-500/20',
        };
      case 'error':
        return {
          icon: <XCircle className="w-6 h-6 text-red-400" />,
          bgColor: 'bg-red-500/20',
        };
      case 'partial':
        return {
          icon: <AlertTriangle className="w-6 h-6 text-amber-400" />,
          bgColor: 'bg-amber-500/20',
        };
    }
  }, [overallStatus]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="bulk-progress-title"
    >
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center gap-3 p-4 border-b border-slate-700">
          <div className={`p-2 rounded-lg ${headerConfig.bgColor}`}>
            {headerConfig.icon}
          </div>
          <div className="flex-1">
            <h2 id="bulk-progress-title" className="text-lg font-semibold text-white">
              {isComplete
                ? overallStatus === 'success'
                  ? 'Operation Complete'
                  : overallStatus === 'error'
                    ? 'Operation Failed'
                    : 'Operation Completed with Errors'
                : labels.title}
            </h2>
            <p className="text-sm text-slate-400">
              {isComplete
                ? `${successCount} template${successCount !== 1 ? 's' : ''} ${labels.pastTense} successfully`
                : `${labels.verb} ${totalItems} template${totalItems !== 1 ? 's' : ''}...`}
            </p>
          </div>
          {isComplete && (
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white transition-colors"
              title="Close"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Progress */}
        <div className="p-4 space-y-4">
          {/* Overall progress bar */}
          <ProgressBar
            value={completedItems}
            max={totalItems}
            color={isComplete ? (failedItems > 0 ? 'red' : 'emerald') : 'violet'}
          />

          {/* Stats summary */}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">{successCount} succeeded</span>
            </div>
            {failedItems > 0 && (
              <div className="flex items-center gap-1.5">
                <XCircle className="w-4 h-4 text-red-400" />
                <span className="text-red-400">{failedItems} failed</span>
              </div>
            )}
          </div>

          {/* Individual items list */}
          {items && items.length > 0 && (
            <div className="max-h-48 overflow-y-auto border border-slate-700 rounded-lg divide-y divide-slate-700">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center gap-2 px-3 py-2 text-sm"
                >
                  <ItemStatusIcon status={item.status} />
                  <span
                    className={`flex-1 truncate ${
                      item.status === 'error' ? 'text-red-400' : 'text-slate-300'
                    }`}
                  >
                    {item.label}
                  </span>
                  {item.error && (
                    <span className="text-xs text-red-400 truncate max-w-32" title={item.error}>
                      {item.error}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Results from batch response */}
          {results && results.some(r => !r.success) && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              <h4 className="text-sm font-medium text-red-400 mb-2">Errors</h4>
              <ul className="text-xs text-red-300 space-y-1 max-h-24 overflow-y-auto">
                {results
                  .filter((r) => !r.success)
                  .map((r) => (
                    <li key={r.index}>
                      Item {r.index + 1}: {r.error || 'Unknown error'}
                    </li>
                  ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-slate-700">
          {!isComplete && onCancel && (
            <button
              onClick={onCancel}
              disabled={isCancelling}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {isCancelling ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Cancelling...
                </>
              ) : (
                <>Cancel</>
              )}
            </button>
          )}
          {isComplete && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default BulkProgressModal;
