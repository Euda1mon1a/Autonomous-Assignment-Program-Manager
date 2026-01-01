'use client';

/**
 * AuditLogTable Component
 *
 * Comprehensive audit log display with sortable columns,
 * expandable rows for change details, and pagination.
 */

import { useState, useCallback, useMemo } from 'react';
import { format } from 'date-fns';
import {
  ChevronDown,
  ChevronUp,
  ChevronRight,
  ArrowUpDown,
  AlertTriangle,
  Info,
  AlertCircle,
  User,
  Calendar,
  FileText,
  Plus,
  Pencil,
  Trash2,
  RotateCcw,
  Upload,
  Download,
  CheckCircle,
  LogIn,
  LogOut,
} from 'lucide-react';
import type {
  AuditLogEntry,
  AuditLogSort,
  AuditActionType,
  AuditSeverity,
  FieldChange,
} from './types';
import {
  ENTITY_TYPE_LABELS,
  ACTION_TYPE_LABELS,
  PAGE_SIZE_OPTIONS,
} from './types';

// ============================================================================
// Types
// ============================================================================

interface AuditLogTableProps {
  logs: AuditLogEntry[];
  total: number;
  page: number;
  pageSize: number;
  sort: AuditLogSort;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onSortChange: (sort: AuditLogSort) => void;
  onEntrySelect?: (entry: AuditLogEntry) => void;
  isLoading?: boolean;
  selectedEntryId?: string;
}

// ============================================================================
// Helper Components
// ============================================================================

/**
 * Get icon component for action type
 */
function ActionIcon({ action }: { action: AuditActionType }) {
  const iconProps = { className: 'w-4 h-4', 'aria-hidden': 'true' as const };

  switch (action) {
    case 'create':
      return <Plus {...iconProps} />;
    case 'update':
      return <Pencil {...iconProps} />;
    case 'delete':
      return <Trash2 {...iconProps} />;
    case 'override':
      return <AlertTriangle {...iconProps} />;
    case 'restore':
      return <RotateCcw {...iconProps} />;
    case 'bulk_import':
      return <Upload {...iconProps} />;
    case 'bulk_delete':
      return <Trash2 {...iconProps} />;
    case 'schedule_generate':
      return <Calendar {...iconProps} />;
    case 'schedule_validate':
      return <CheckCircle {...iconProps} />;
    case 'login':
      return <LogIn {...iconProps} />;
    case 'logout':
      return <LogOut {...iconProps} />;
    case 'export':
      return <Download {...iconProps} />;
    default:
      return <FileText {...iconProps} />;
  }
}

/**
 * Severity badge component
 */
function SeverityBadge({ severity }: { severity: AuditSeverity }) {
  const config = {
    info: {
      bg: 'bg-blue-100',
      text: 'text-blue-800',
      icon: <Info className="w-3 h-3" aria-hidden="true" />,
    },
    warning: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      icon: <AlertTriangle className="w-3 h-3" aria-hidden="true" />,
    },
    critical: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      icon: <AlertCircle className="w-3 h-3" aria-hidden="true" />,
    },
  };

  const { bg, text, icon } = config[severity];

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${bg} ${text}`}
    >
      {icon}
      {severity}
    </span>
  );
}

/**
 * Action badge component
 */
function ActionBadge({ action }: { action: AuditActionType }) {
  const colorMap: Record<AuditActionType, string> = {
    create: 'bg-green-100 text-green-800',
    update: 'bg-blue-100 text-blue-800',
    delete: 'bg-red-100 text-red-800',
    override: 'bg-orange-100 text-orange-800',
    restore: 'bg-purple-100 text-purple-800',
    bulk_import: 'bg-indigo-100 text-indigo-800',
    bulk_delete: 'bg-red-100 text-red-800',
    schedule_generate: 'bg-teal-100 text-teal-800',
    schedule_validate: 'bg-cyan-100 text-cyan-800',
    login: 'bg-gray-100 text-gray-800',
    logout: 'bg-gray-100 text-gray-800',
    export: 'bg-violet-100 text-violet-800',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${colorMap[action]}`}
    >
      <ActionIcon action={action} />
      {ACTION_TYPE_LABELS[action]}
    </span>
  );
}

/**
 * Change detail row component
 */
function ChangeDetail({ change }: { change: FieldChange }) {
  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return '(empty)';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  return (
    <div className="grid grid-cols-3 gap-4 py-2 text-sm border-b border-gray-100 last:border-0">
      <div className="font-medium text-gray-700">
        {change.displayName || change.field}
      </div>
      <div className="text-red-600 line-through">
        {formatValue(change.oldValue)}
      </div>
      <div className="text-green-600">
        {formatValue(change.newValue)}
      </div>
    </div>
  );
}

/**
 * Expandable row component
 */
function ExpandableRow({
  entry,
  isExpanded,
  onToggle,
  onSelect,
  isSelected,
}: {
  entry: AuditLogEntry;
  isExpanded: boolean;
  onToggle: () => void;
  onSelect?: () => void;
  isSelected: boolean;
}) {
  const hasChanges = entry.changes && entry.changes.length > 0;
  const hasDetails = hasChanges || entry.reason || entry.acgmeOverride;

  return (
    <>
      <tr
        className={`
          border-b border-gray-200 hover:bg-gray-50 cursor-pointer
          ${isSelected ? 'bg-blue-50' : ''}
          ${entry.acgmeOverride ? 'bg-orange-50' : ''}
        `}
        onClick={onSelect}
        role="row"
      >
        <td className="px-4 py-3" role="cell">
          {hasDetails && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggle();
              }}
              className="p-1 hover:bg-gray-200 rounded"
              aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
              aria-expanded={isExpanded}
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" aria-hidden="true" />
              ) : (
                <ChevronRight className="w-4 h-4" aria-hidden="true" />
              )}
            </button>
          )}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600" role="cell">
          {format(new Date(entry.timestamp), 'MMM d, yyyy HH:mm:ss')}
        </td>
        <td className="px-4 py-3" role="cell">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-gray-400" aria-hidden="true" />
            <span className="text-sm font-medium">{entry.user.name}</span>
          </div>
        </td>
        <td className="px-4 py-3" role="cell">
          <ActionBadge action={entry.action} />
        </td>
        <td className="px-4 py-3 text-sm" role="cell">
          <span className="text-gray-600">
            {ENTITY_TYPE_LABELS[entry.entityType]}
          </span>
          {entry.entityName && (
            <span className="ml-1 text-gray-900 font-medium">
              ({entry.entityName})
            </span>
          )}
        </td>
        <td className="px-4 py-3" role="cell">
          <SeverityBadge severity={entry.severity} />
        </td>
        <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate" role="cell">
          {entry.reason || '-'}
        </td>
      </tr>
      {isExpanded && hasDetails && (
        <tr className="bg-gray-50" role="row">
          <td colSpan={7} className="px-4 py-4" role="cell">
            <div className="ml-8 space-y-4">
              {entry.acgmeOverride && (
                <div className="bg-orange-100 border border-orange-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-orange-800 font-medium mb-1">
                    <AlertTriangle className="w-4 h-4" aria-hidden="true" />
                    ACGME Override
                  </div>
                  {entry.acgmeJustification && (
                    <p className="text-sm text-orange-700">
                      {entry.acgmeJustification}
                    </p>
                  )}
                </div>
              )}
              {entry.reason && (
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="text-sm font-medium text-gray-700 mb-1">
                    Reason
                  </div>
                  <p className="text-sm text-gray-600">{entry.reason}</p>
                </div>
              )}
              {hasChanges && (
                <div className="bg-white border border-gray-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    Changes
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-xs font-semibold text-gray-500 pb-2 border-b border-gray-200">
                    <div>Field</div>
                    <div>Previous Value</div>
                    <div>New Value</div>
                  </div>
                  {entry.changes!.map((change, idx) => (
                    <ChangeDetail key={idx} change={change} />
                  ))}
                </div>
              )}
              {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="text-sm font-medium text-gray-700 mb-1">
                    Additional Details
                  </div>
                  <pre className="text-xs text-gray-600 overflow-x-auto">
                    {JSON.stringify(entry.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function AuditLogTable({
  logs,
  total,
  page,
  pageSize,
  sort,
  onPageChange,
  onPageSizeChange,
  onSortChange,
  onEntrySelect,
  isLoading = false,
  selectedEntryId,
}: AuditLogTableProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const totalPages = Math.ceil(total / pageSize);

  const toggleExpanded = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleSort = useCallback(
    (field: AuditLogSort['field']) => {
      onSortChange({
        field,
        direction:
          sort.field === field && sort.direction === 'desc' ? 'asc' : 'desc',
      });
    },
    [sort, onSortChange]
  );

  const SortableHeader = ({
    field,
    children,
  }: {
    field: AuditLogSort['field'];
    children: React.ReactNode;
  }) => (
    <th
      className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
      onClick={() => handleSort(field)}
      role="columnheader"
      aria-sort={
        sort.field === field
          ? sort.direction === 'desc'
            ? 'descending'
            : 'ascending'
          : 'none'
      }
    >
      <div className="flex items-center gap-1">
        {children}
        {sort.field === field ? (
          sort.direction === 'desc' ? (
            <ChevronDown className="w-4 h-4" aria-hidden="true" />
          ) : (
            <ChevronUp className="w-4 h-4" aria-hidden="true" />
          )
        ) : (
          <ArrowUpDown className="w-4 h-4 text-gray-400" aria-hidden="true" />
        )}
      </div>
    </th>
  );

  // Pagination range
  const pageRange = useMemo(() => {
    const range: number[] = [];
    const start = Math.max(1, page - 2);
    const end = Math.min(totalPages, page + 2);
    for (let i = start; i <= end; i++) {
      range.push(i);
    }
    return range;
  }, [page, totalPages]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="animate-pulse">
          <div className="h-12 bg-gray-100 border-b" />
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 border-b border-gray-100">
              <div className="flex items-center gap-4 p-4">
                <div className="w-6 h-6 bg-gray-200 rounded" />
                <div className="flex-1 h-4 bg-gray-200 rounded" />
                <div className="w-24 h-4 bg-gray-200 rounded" />
                <div className="w-20 h-6 bg-gray-200 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" aria-hidden="true" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">
          No audit logs found
        </h3>
        <p className="text-gray-600">
          Try adjusting your filters or date range.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full" role="table" aria-label="Audit log entries">
          <thead className="bg-gray-50 border-b border-gray-200" role="rowgroup">
            <tr role="row">
              <th className="w-10 px-4 py-3" role="columnheader" aria-label="Expand row" />
              <SortableHeader field="timestamp">Timestamp</SortableHeader>
              <SortableHeader field="user">User</SortableHeader>
              <SortableHeader field="action">Action</SortableHeader>
              <SortableHeader field="entityType">Entity</SortableHeader>
              <SortableHeader field="severity">Severity</SortableHeader>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider" role="columnheader">
                Reason
              </th>
            </tr>
          </thead>
          <tbody role="rowgroup">
            {logs.map((log) => (
              <ExpandableRow
                key={log.id}
                entry={log}
                isExpanded={expandedIds.has(log.id)}
                onToggle={() => toggleExpanded(log.id)}
                onSelect={onEntrySelect ? () => onEntrySelect(log) : undefined}
                isSelected={selectedEntryId === log.id}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Show</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Select page size"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
          <span>entries</span>
          <span className="ml-4">
            Showing {(page - 1) * pageSize + 1} to{' '}
            {Math.min(page * pageSize, total)} of {total} entries
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => onPageChange(1)}
            disabled={page === 1}
            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Go to first page"
          >
            First
          </button>
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Go to previous page"
          >
            Previous
          </button>
          {pageRange.map((p) => (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`px-3 py-1 text-sm border rounded ${
                p === page
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'border-gray-300 hover:bg-gray-50'
              }`}
              aria-label={`Go to page ${p}`}
              aria-current={p === page ? 'page' : undefined}
            >
              {p}
            </button>
          ))}
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page === totalPages}
            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Go to next page"
          >
            Next
          </button>
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={page === totalPages}
            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Go to last page"
          >
            Last
          </button>
        </div>
      </div>
    </div>
  );
}
