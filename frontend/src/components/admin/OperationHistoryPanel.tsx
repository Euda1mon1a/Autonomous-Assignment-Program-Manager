'use client';

/**
 * OperationHistoryPanel Component
 *
 * Displays recent bulk operations with the ability to undo them.
 * Shows operation type, timestamp, affected templates, and undo status.
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  History,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Trash2,
  Edit2,
  Copy,
  Archive,
  Upload,
  Plus,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react';
import type { BulkOperationType } from './BulkProgressModal';

// ============================================================================
// Types
// ============================================================================

export interface OperationRecord {
  id: string;
  type: BulkOperationType | 'import';
  timestamp: Date;
  templateIds: string[];
  templateNames: string[];
  status: 'success' | 'failed' | 'undone';
  canUndo: boolean;
  undoDeadline?: Date;
  details?: string;
}

export interface OperationHistoryPanelProps {
  /** Operation records */
  operations: OperationRecord[];
  /** Callback to undo an operation */
  onUndo: (operationId: string) => Promise<void>;
  /** Callback to clear history */
  onClearHistory?: () => void;
  /** Whether panel is loading */
  isLoading?: boolean;
  /** ID of operation being undone */
  undoingId?: string | null;
  /** Maximum operations to show */
  maxItems?: number;
}

// ============================================================================
// Constants
// ============================================================================

const OPERATION_ICONS: Record<BulkOperationType | 'import', typeof History> = {
  delete: Trash2,
  update: Edit2,
  create: Plus,
  archive: Archive,
  restore: RotateCcw,
  duplicate: Copy,
  import: Upload,
};

const OPERATION_LABELS: Record<BulkOperationType | 'import', string> = {
  delete: 'Deleted',
  update: 'Updated',
  create: 'Created',
  archive: 'Archived',
  restore: 'Restored',
  duplicate: 'Duplicated',
  import: 'Imported',
};

const OPERATION_COLORS: Record<BulkOperationType | 'import', string> = {
  delete: 'text-red-400',
  update: 'text-blue-400',
  create: 'text-emerald-400',
  archive: 'text-amber-400',
  restore: 'text-cyan-400',
  duplicate: 'text-violet-400',
  import: 'text-green-400',
};

// ============================================================================
// Helper Functions
// ============================================================================

function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString();
}

function getUndoTimeRemaining(deadline: Date): string | null {
  const now = new Date();
  const diffMs = deadline.getTime() - now.getTime();

  if (diffMs <= 0) return null;

  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);

  if (diffSec < 60) return `${diffSec}s`;
  return `${diffMin}m ${diffSec % 60}s`;
}

// ============================================================================
// Subcomponents
// ============================================================================

interface OperationItemProps {
  operation: OperationRecord;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onUndo: () => void;
  isUndoing: boolean;
}

function OperationItem({
  operation,
  isExpanded,
  onToggleExpand,
  onUndo,
  isUndoing,
}: OperationItemProps) {
  const Icon = OPERATION_ICONS[operation.type];
  const label = OPERATION_LABELS[operation.type];
  const color = OPERATION_COLORS[operation.type];

  const [undoTimeRemaining, setUndoTimeRemaining] = useState<string | null>(
    operation.undoDeadline ? getUndoTimeRemaining(operation.undoDeadline) : null
  );

  // Update undo countdown
  React.useEffect(() => {
    if (!operation.undoDeadline || !operation.canUndo) return;

    const interval = setInterval(() => {
      const remaining = getUndoTimeRemaining(operation.undoDeadline!);
      setUndoTimeRemaining(remaining);
    }, 1000);

    return () => clearInterval(interval);
  }, [operation.undoDeadline, operation.canUndo]);

  return (
    <div
      className={`
        border rounded-lg transition-colors
        ${operation.status === 'undone' ? 'border-slate-700/50 opacity-60' : 'border-slate-700'}
      `}
    >
      {/* Row header */}
      <div
        className="flex items-center gap-3 p-3 cursor-pointer hover:bg-slate-700/30 transition-colors"
        onClick={onToggleExpand}
      >
        <button
          type="button"
          className="p-1 text-slate-400"
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
        >
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        <div className={`p-1.5 rounded ${color.replace('text-', 'bg-').replace('-400', '-500/20')}`}>
          <Icon className={`w-4 h-4 ${color}`} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium ${color}`}>{label}</span>
            <span className="text-sm text-slate-400">
              {operation.templateIds.length} template{operation.templateIds.length !== 1 ? 's' : ''}
            </span>
            {operation.status === 'undone' && (
              <span className="px-1.5 py-0.5 bg-slate-700 rounded text-xs text-slate-400">
                Undone
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <Clock className="w-3 h-3 text-slate-500" />
            <span className="text-xs text-slate-500">
              {formatRelativeTime(operation.timestamp)}
            </span>
          </div>
        </div>

        {operation.canUndo && operation.status !== 'undone' && (
          <div className="flex items-center gap-2">
            {undoTimeRemaining && (
              <span className="text-xs text-amber-400">{undoTimeRemaining}</span>
            )}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onUndo();
              }}
              disabled={isUndoing}
              className="flex items-center gap-1 px-2 py-1 text-sm text-violet-400 hover:text-violet-300 transition-colors disabled:opacity-50"
            >
              {isUndoing ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <RotateCcw className="w-3 h-3" />
              )}
              Undo
            </button>
          </div>
        )}

        {operation.status === 'success' && !operation.canUndo && (
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        )}
        {operation.status === 'failed' && (
          <XCircle className="w-4 h-4 text-red-400" />
        )}
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-4 pb-3 border-t border-slate-700/50">
          <p className="text-xs text-slate-400 mt-3 mb-2">Affected templates:</p>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
            {operation.templateNames.map((name, i) => (
              <span
                key={i}
                className="px-2 py-0.5 bg-slate-700 rounded text-xs text-slate-300"
              >
                {name}
              </span>
            ))}
          </div>
          {operation.details && (
            <p className="text-xs text-slate-500 mt-2">{operation.details}</p>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function OperationHistoryPanel({
  operations,
  onUndo,
  onClearHistory,
  isLoading = false,
  undoingId = null,
  maxItems = 20,
}: OperationHistoryPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const displayOperations = useMemo(() => {
    const sorted = [...operations].sort(
      (a, b) => b.timestamp.getTime() - a.timestamp.getTime()
    );
    return showAll ? sorted : sorted.slice(0, maxItems);
  }, [operations, showAll, maxItems]);

  const handleToggleExpand = useCallback((id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  }, []);

  const handleUndo = useCallback(
    async (operationId: string) => {
      await onUndo(operationId);
    },
    [onUndo]
  );

  if (isLoading) {
    return (
      <div className="p-6 bg-slate-800/50 border border-slate-700 rounded-xl">
        <div className="flex items-center justify-center h-24">
          <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-slate-400" />
          <h3 className="text-sm font-medium text-white">Operation History</h3>
          <span className="px-1.5 py-0.5 bg-slate-700 rounded text-xs text-slate-400">
            {operations.length}
          </span>
        </div>
        {onClearHistory && operations.length > 0 && (
          <button
            type="button"
            onClick={onClearHistory}
            className="text-xs text-slate-400 hover:text-white transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {operations.length === 0 ? (
          <div className="text-center py-6">
            <History className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-400">No recent operations</p>
          </div>
        ) : (
          <div className="space-y-2">
            {displayOperations.map((operation) => (
              <OperationItem
                key={operation.id}
                operation={operation}
                isExpanded={expandedId === operation.id}
                onToggleExpand={() => handleToggleExpand(operation.id)}
                onUndo={() => handleUndo(operation.id)}
                isUndoing={undoingId === operation.id}
              />
            ))}

            {!showAll && operations.length > maxItems && (
              <button
                type="button"
                onClick={() => setShowAll(true)}
                className="w-full py-2 text-sm text-violet-400 hover:text-violet-300 transition-colors"
              >
                Show {operations.length - maxItems} more
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default OperationHistoryPanel;
