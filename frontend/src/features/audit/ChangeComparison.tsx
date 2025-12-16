'use client';

/**
 * ChangeComparison Component
 *
 * Side-by-side comparison view for audit log entries,
 * showing detailed changes between states or between two entries.
 */

import { useMemo } from 'react';
import { format, parseISO } from 'date-fns';
import {
  ArrowRight,
  ArrowLeftRight,
  User,
  Calendar,
  AlertTriangle,
  X,
  Minus,
  Plus,
  Equal,
  FileText,
  Info,
} from 'lucide-react';
import type { AuditLogEntry, FieldChange } from './types';
import { ENTITY_TYPE_LABELS, ACTION_TYPE_LABELS } from './types';

// ============================================================================
// Types
// ============================================================================

interface ChangeComparisonProps {
  entry: AuditLogEntry;
  compareWith?: AuditLogEntry;
  onClose?: () => void;
  onClearComparison?: () => void;
}

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged' | 'modified';
  field: string;
  displayName?: string;
  oldValue?: unknown;
  newValue?: unknown;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Format a value for display
 */
function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '(empty)';
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.length === 0 ? '(empty array)' : value.join(', ');
    }
    return JSON.stringify(value, null, 2);
  }
  if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
    try {
      return format(parseISO(value), 'MMM d, yyyy HH:mm');
    } catch {
      return value;
    }
  }
  return String(value);
}

/**
 * Determine if two values are equal
 */
function areValuesEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a === null || a === undefined) return b === null || b === undefined;
  if (typeof a === 'object' && typeof b === 'object') {
    return JSON.stringify(a) === JSON.stringify(b);
  }
  return false;
}

/**
 * Build diff lines from changes
 */
function buildDiffLines(changes?: FieldChange[]): DiffLine[] {
  if (!changes || changes.length === 0) {
    return [];
  }

  return changes.map((change) => ({
    type: 'modified' as const,
    field: change.field,
    displayName: change.displayName,
    oldValue: change.oldValue,
    newValue: change.newValue,
  }));
}

/**
 * Compare two audit entries
 */
function compareEntries(
  entry1: AuditLogEntry,
  entry2: AuditLogEntry
): DiffLine[] {
  const lines: DiffLine[] = [];

  // Compare metadata fields
  const metaFields = [
    { key: 'action', label: 'Action' },
    { key: 'entityType', label: 'Entity Type' },
    { key: 'entityName', label: 'Entity Name' },
    { key: 'severity', label: 'Severity' },
    { key: 'reason', label: 'Reason' },
  ];

  metaFields.forEach(({ key, label }) => {
    const val1 = (entry1 as unknown as Record<string, unknown>)[key];
    const val2 = (entry2 as unknown as Record<string, unknown>)[key];

    if (!areValuesEqual(val1, val2)) {
      lines.push({
        type: 'modified',
        field: key,
        displayName: label,
        oldValue: val1,
        newValue: val2,
      });
    }
  });

  // Merge changes from both entries
  const allChanges = new Map<string, { old?: unknown; new?: unknown }>();

  entry1.changes?.forEach((c) => {
    allChanges.set(c.field, { old: c.oldValue, new: c.newValue });
  });

  entry2.changes?.forEach((c) => {
    const existing = allChanges.get(c.field);
    if (existing) {
      existing.new = c.newValue;
    } else {
      allChanges.set(c.field, { old: c.oldValue, new: c.newValue });
    }
  });

  allChanges.forEach((values, field) => {
    lines.push({
      type: areValuesEqual(values.old, values.new) ? 'unchanged' : 'modified',
      field,
      oldValue: values.old,
      newValue: values.new,
    });
  });

  return lines;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Entry header card
 */
function EntryHeader({
  entry,
  label,
}: {
  entry: AuditLogEntry;
  label: string;
}) {
  const timestamp = format(parseISO(entry.timestamp), 'MMM d, yyyy HH:mm:ss');

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="font-semibold text-gray-900">
        {ACTION_TYPE_LABELS[entry.action]}
      </div>
      <div className="text-sm text-gray-600">
        {ENTITY_TYPE_LABELS[entry.entityType]}
        {entry.entityName && <span className="font-medium"> · {entry.entityName}</span>}
      </div>
      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
        <span className="flex items-center gap-1">
          <Calendar className="w-4 h-4" />
          {timestamp}
        </span>
        <span className="flex items-center gap-1">
          <User className="w-4 h-4" />
          {entry.user.name}
        </span>
      </div>
      {entry.acgmeOverride && (
        <div className="mt-2 flex items-center gap-1 text-sm text-orange-600">
          <AlertTriangle className="w-4 h-4" />
          ACGME Override
        </div>
      )}
    </div>
  );
}

/**
 * Single diff line component
 */
function DiffLineRow({ line }: { line: DiffLine }) {
  const typeConfig = {
    added: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      icon: <Plus className="w-4 h-4 text-green-600" />,
      label: 'Added',
    },
    removed: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      icon: <Minus className="w-4 h-4 text-red-600" />,
      label: 'Removed',
    },
    modified: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      icon: <ArrowRight className="w-4 h-4 text-yellow-600" />,
      label: 'Changed',
    },
    unchanged: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      icon: <Equal className="w-4 h-4 text-gray-400" />,
      label: 'Unchanged',
    },
  };

  const config = typeConfig[line.type];

  return (
    <div className={`p-3 rounded-lg border ${config.bg} ${config.border}`}>
      <div className="flex items-center gap-2 mb-2">
        {config.icon}
        <span className="font-medium text-gray-700">
          {line.displayName || line.field}
        </span>
        <span className="text-xs text-gray-500">({config.label})</span>
      </div>

      {line.type === 'modified' && (
        <div className="grid grid-cols-2 gap-4 mt-2">
          <div className="p-2 bg-red-100 rounded border border-red-200">
            <div className="text-xs text-red-600 mb-1">Before</div>
            <div className="text-sm text-red-800 font-mono break-all">
              {formatValue(line.oldValue)}
            </div>
          </div>
          <div className="p-2 bg-green-100 rounded border border-green-200">
            <div className="text-xs text-green-600 mb-1">After</div>
            <div className="text-sm text-green-800 font-mono break-all">
              {formatValue(line.newValue)}
            </div>
          </div>
        </div>
      )}

      {line.type === 'added' && (
        <div className="p-2 bg-green-100 rounded border border-green-200">
          <div className="text-sm text-green-800 font-mono break-all">
            {formatValue(line.newValue)}
          </div>
        </div>
      )}

      {line.type === 'removed' && (
        <div className="p-2 bg-red-100 rounded border border-red-200">
          <div className="text-sm text-red-800 font-mono break-all line-through">
            {formatValue(line.oldValue)}
          </div>
        </div>
      )}

      {line.type === 'unchanged' && (
        <div className="p-2 bg-gray-100 rounded">
          <div className="text-sm text-gray-600 font-mono break-all">
            {formatValue(line.oldValue ?? line.newValue)}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Side by side comparison view
 */
function SideBySideView({
  entry,
  compareWith,
}: {
  entry: AuditLogEntry;
  compareWith: AuditLogEntry;
}) {
  const diffLines = useMemo(
    () => compareEntries(entry, compareWith),
    [entry, compareWith]
  );

  return (
    <div className="space-y-4">
      {/* Headers */}
      <div className="grid grid-cols-2 gap-4">
        <EntryHeader entry={entry} label="Earlier Entry" />
        <EntryHeader entry={compareWith} label="Later Entry" />
      </div>

      {/* Arrow indicator */}
      <div className="flex items-center justify-center">
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-full">
          <ArrowLeftRight className="w-5 h-5 text-gray-500" />
          <span className="text-sm text-gray-600">Comparing changes</span>
        </div>
      </div>

      {/* Differences */}
      {diffLines.length > 0 ? (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-700">Differences</h4>
          {diffLines.map((line, idx) => (
            <DiffLineRow key={idx} line={line} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <Info className="w-8 h-8 mx-auto mb-2" />
          <p>No differences found between these entries</p>
        </div>
      )}
    </div>
  );
}

/**
 * Single entry change view
 */
function SingleEntryView({ entry }: { entry: AuditLogEntry }) {
  const diffLines = useMemo(() => buildDiffLines(entry.changes), [entry.changes]);

  return (
    <div className="space-y-4">
      {/* Entry header */}
      <EntryHeader entry={entry} label="Entry Details" />

      {/* Reason */}
      {entry.reason && (
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-sm font-medium text-gray-700 mb-1">Reason</div>
          <p className="text-gray-600">{entry.reason}</p>
        </div>
      )}

      {/* ACGME Override info */}
      {entry.acgmeOverride && (
        <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
          <div className="flex items-center gap-2 text-orange-800 font-medium mb-2">
            <AlertTriangle className="w-5 h-5" />
            ACGME Compliance Override
          </div>
          {entry.acgmeJustification && (
            <p className="text-orange-700">{entry.acgmeJustification}</p>
          )}
        </div>
      )}

      {/* Changes */}
      {diffLines.length > 0 ? (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-700">
            Changes ({diffLines.length} field{diffLines.length !== 1 ? 's' : ''})
          </h4>
          {diffLines.map((line, idx) => (
            <DiffLineRow key={idx} line={line} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
          <FileText className="w-8 h-8 mx-auto mb-2" />
          <p>No detailed changes recorded for this entry</p>
        </div>
      )}

      {/* Metadata */}
      {entry.metadata && Object.keys(entry.metadata).length > 0 && (
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-sm font-medium text-gray-700 mb-2">
            Additional Metadata
          </div>
          <pre className="text-xs text-gray-600 overflow-x-auto bg-white p-3 rounded border">
            {JSON.stringify(entry.metadata, null, 2)}
          </pre>
        </div>
      )}

      {/* Technical details */}
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="text-sm font-medium text-gray-700 mb-2">
          Technical Details
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Entry ID:</span>
            <span className="ml-2 font-mono text-gray-700">{entry.id}</span>
          </div>
          <div>
            <span className="text-gray-500">Entity ID:</span>
            <span className="ml-2 font-mono text-gray-700">{entry.entityId}</span>
          </div>
          {entry.ipAddress && (
            <div>
              <span className="text-gray-500">IP Address:</span>
              <span className="ml-2 font-mono text-gray-700">{entry.ipAddress}</span>
            </div>
          )}
          {entry.sessionId && (
            <div>
              <span className="text-gray-500">Session ID:</span>
              <span className="ml-2 font-mono text-gray-700">{entry.sessionId}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function ChangeComparison({
  entry,
  compareWith,
  onClose,
  onClearComparison,
}: ChangeComparisonProps) {
  const isComparingTwo = !!compareWith;

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          {isComparingTwo ? (
            <>
              <ArrowLeftRight className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-gray-900">Compare Entries</h3>
            </>
          ) : (
            <>
              <FileText className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-gray-900">Entry Details</h3>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isComparingTwo && onClearComparison && (
            <button
              type="button"
              onClick={onClearComparison}
              className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded transition-colors"
            >
              Clear comparison
            </button>
          )}
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 max-h-[600px] overflow-y-auto">
        {isComparingTwo ? (
          <SideBySideView entry={entry} compareWith={compareWith} />
        ) : (
          <SingleEntryView entry={entry} />
        )}
      </div>
    </div>
  );
}
