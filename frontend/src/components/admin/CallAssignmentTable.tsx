'use client';

/**
 * CallAssignmentTable Component
 *
 * Displays faculty call assignments in a sortable table with row selection
 * for bulk operations. Follows the dark theme pattern from admin scheduling page.
 */
import React, { useMemo, useCallback } from 'react';
import {
  ChevronUp,
  ChevronDown,
  Edit2,
  Trash2,
  Calendar,
} from 'lucide-react';
import type {
  CallAssignment,
  CallSortField,
  SortDirection,
  CallType,
  PostCallStatus,
} from '@/types/faculty-call';
import { getCallTypeConfig, getPostCallStatusConfig } from '@/types/faculty-call';

// ============================================================================
// Types
// ============================================================================

export interface CallAssignmentTableProps {
  /** List of call assignments to display */
  assignments: CallAssignment[];
  /** Currently selected assignment IDs */
  selectedIds: string[];
  /** Callback when selection changes */
  onSelectionChange: (ids: string[]) => void;
  /** Current sort configuration */
  sort: { field: CallSortField; direction: SortDirection };
  /** Callback when sort changes */
  onSortChange: (field: CallSortField) => void;
  /** Callback when row is clicked */
  onRowClick?: (assignment: CallAssignment) => void;
  /** Callback to edit assignment */
  onEdit?: (assignment: CallAssignment) => void;
  /** Callback to delete single assignment */
  onDelete?: (assignment: CallAssignment) => void;
  /** Whether table is in loading state */
  isLoading?: boolean;
}

// ============================================================================
// Subcomponents
// ============================================================================

interface SortHeaderProps {
  label: string;
  field: CallSortField;
  currentSort: { field: CallSortField; direction: SortDirection };
  onSort: (field: CallSortField) => void;
}

function SortHeader({ label, field, currentSort, onSort }: SortHeaderProps) {
  const isActive = currentSort.field === field;

  return (
    <button
      onClick={() => onSort(field)}
      className="flex items-center gap-1 text-left font-medium hover:text-white transition-colors"
    >
      {label}
      <span className="flex flex-col">
        <ChevronUp
          className={`w-3 h-3 -mb-1 ${
            isActive && currentSort.direction === 'asc'
              ? 'text-violet-400'
              : 'text-slate-600'
          }`}
        />
        <ChevronDown
          className={`w-3 h-3 ${
            isActive && currentSort.direction === 'desc'
              ? 'text-violet-400'
              : 'text-slate-600'
          }`}
        />
      </span>
    </button>
  );
}

interface CallTypeBadgeProps {
  callType: CallType;
}

function CallTypeBadge({ callType }: CallTypeBadgeProps) {
  const config = getCallTypeConfig(callType);

  return (
    <span
      className={`
        inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
        ${config.bgColor} ${config.color}
      `}
    >
      {config.label}
    </span>
  );
}

interface PostCallStatusBadgeProps {
  status: PostCallStatus;
}

function PostCallStatusBadge({ status }: PostCallStatusBadgeProps) {
  const config = getPostCallStatusConfig(status);

  return (
    <span
      className={`
        inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
        ${config.bgColor} ${config.color}
      `}
    >
      {config.label}
    </span>
  );
}

interface RowCheckboxProps {
  checked: boolean;
  indeterminate?: boolean;
  onChange: () => void;
  ariaLabel: string;
}

function RowCheckbox({
  checked,
  indeterminate,
  onChange,
  ariaLabel,
}: RowCheckboxProps) {
  const checkboxRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (checkboxRef.current) {
      checkboxRef.current.indeterminate = indeterminate || false;
    }
  }, [indeterminate]);

  return (
    <input
      ref={checkboxRef}
      type="checkbox"
      checked={checked}
      onChange={onChange}
      aria-label={ariaLabel}
      className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
    />
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function CallAssignmentTable({
  assignments,
  selectedIds,
  onSelectionChange,
  sort,
  onSortChange,
  onRowClick,
  onEdit,
  onDelete,
  isLoading = false,
}: CallAssignmentTableProps) {
  // Selection helpers
  const allSelected = useMemo(
    () => assignments.length > 0 && selectedIds.length === assignments.length,
    [assignments.length, selectedIds.length]
  );

  const someSelected = useMemo(
    () => selectedIds.length > 0 && selectedIds.length < assignments.length,
    [selectedIds.length, assignments.length]
  );

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(assignments.map((a) => a.id));
    }
  }, [allSelected, assignments, onSelectionChange]);

  const handleSelectRow = useCallback(
    (id: string) => {
      if (selectedIds.includes(id)) {
        onSelectionChange(selectedIds.filter((i) => i !== id));
      } else {
        onSelectionChange([...selectedIds, id]);
      }
    },
    [selectedIds, onSelectionChange]
  );

  const handleRowClick = useCallback(
    (assignment: CallAssignment, event: React.MouseEvent) => {
      // Ignore clicks on checkboxes and action buttons
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'BUTTON' ||
        target.closest('button')
      ) {
        return;
      }
      onRowClick?.(assignment);
    },
    [onRowClick]
  );

  if (isLoading) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        <div className="animate-pulse">
          <div className="h-12 bg-slate-700/50" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 border-t border-slate-700/50">
              <div className="h-full flex items-center px-4 gap-4">
                <div className="w-4 h-4 bg-slate-700 rounded" />
                <div className="flex-1 h-4 bg-slate-700 rounded" />
                <div className="w-20 h-4 bg-slate-700 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (assignments.length === 0) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-12 text-center">
        <Calendar className="w-12 h-12 text-slate-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">
          No call assignments found
        </h3>
        <p className="text-slate-400">
          Adjust your filters or create new call assignments.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
      <div className="overflow-x-auto max-h-[calc(100vh-300px)]">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-slate-800 border-b border-slate-700">
              <th className="w-12 py-3 px-4">
                <RowCheckbox
                  checked={allSelected}
                  indeterminate={someSelected}
                  onChange={handleSelectAll}
                  ariaLabel={allSelected ? 'Deselect all' : 'Select all'}
                />
              </th>
              <th className="text-left py-3 px-4 text-slate-400">
                <SortHeader
                  label="Date"
                  field="date"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">
                Day of Week
              </th>
              <th className="text-left py-3 px-4 text-slate-400">
                <SortHeader
                  label="Person"
                  field="person_name"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="text-left py-3 px-4 text-slate-400">
                <SortHeader
                  label="Call Type"
                  field="call_type"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">
                Post-Call Status
              </th>
              <th className="text-right py-3 px-4 text-slate-400 font-medium">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {assignments.map((assignment) => {
              const isSelected = selectedIds.includes(assignment.id);

              return (
                <tr
                  key={assignment.id}
                  onClick={(e) => handleRowClick(assignment, e)}
                  className={`
                    border-b border-slate-700/50 transition-colors cursor-pointer
                    ${isSelected ? 'bg-violet-500/10' : 'hover:bg-slate-800/50'}
                  `}
                >
                  <td className="py-3 px-4">
                    <RowCheckbox
                      checked={isSelected}
                      onChange={() => handleSelectRow(assignment.id)}
                      ariaLabel={`Select ${assignment.personName} on ${assignment.date}`}
                    />
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-white font-medium">
                      {new Date(assignment.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {assignment.dayOfWeek}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-white font-medium">
                      {assignment.personName}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <CallTypeBadge callType={assignment.call_type} />
                  </td>
                  <td className="py-3 px-4">
                    <PostCallStatusBadge status={assignment.post_call_status} />
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-1">
                      {onEdit && (
                        <button
                          onClick={() => onEdit(assignment)}
                          className="p-1.5 text-slate-400 hover:text-white transition-colors"
                          title="Edit assignment"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      )}
                      {onDelete && (
                        <button
                          onClick={() => onDelete(assignment)}
                          className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
                          title="Delete assignment"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Selection summary */}
      {selectedIds.length > 0 && (
        <div className="bg-violet-500/10 border-t border-violet-500/30 px-4 py-2 text-sm text-violet-300">
          {selectedIds.length} assignment{selectedIds.length !== 1 ? 's' : ''}{' '}
          selected
        </div>
      )}
    </div>
  );
}

export default CallAssignmentTable;
