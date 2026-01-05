'use client';

/**
 * TemplateTable Component
 *
 * Displays rotation templates in a sortable, filterable table with row selection
 * for bulk operations. Follows the dark theme pattern from admin scheduling page.
 */
import React, { useMemo, useCallback } from 'react';
import {
  ChevronUp,
  ChevronDown,
  Edit2,
  Trash2,
  Eye,
  Calendar,
  Settings,
} from 'lucide-react';
import type {
  RotationTemplate,
  SortField,
  SortDirection,
  ActivityType,
} from '@/types/admin-templates';
import { getActivityTypeConfig } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export interface TemplateTableProps {
  /** List of templates to display */
  templates: RotationTemplate[];
  /** Currently selected template IDs */
  selectedIds: string[];
  /** Callback when selection changes */
  onSelectionChange: (ids: string[]) => void;
  /** Current sort configuration */
  sort: { field: SortField; direction: SortDirection };
  /** Callback when sort changes */
  onSortChange: (field: SortField) => void;
  /** Callback to view template details */
  onView?: (template: RotationTemplate) => void;
  /** Callback to edit template */
  onEdit?: (template: RotationTemplate) => void;
  /** Callback to edit template patterns */
  onEditPatterns?: (template: RotationTemplate) => void;
  /** Callback to edit template preferences */
  onEditPreferences?: (template: RotationTemplate) => void;
  /** Callback to delete single template */
  onDelete?: (template: RotationTemplate) => void;
  /** Whether table is in loading state */
  isLoading?: boolean;
}

// ============================================================================
// Subcomponents
// ============================================================================

interface SortHeaderProps {
  label: string;
  field: SortField;
  currentSort: { field: SortField; direction: SortDirection };
  onSort: (field: SortField) => void;
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

interface ActivityTypeBadgeProps {
  activityType: ActivityType;
}

function ActivityTypeBadge({ activityType }: ActivityTypeBadgeProps) {
  const config = getActivityTypeConfig(activityType);

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

export function TemplateTable({
  templates,
  selectedIds,
  onSelectionChange,
  sort,
  onSortChange,
  onView,
  onEdit,
  onEditPatterns,
  onEditPreferences,
  onDelete,
  isLoading = false,
}: TemplateTableProps) {
  // Selection helpers
  const allSelected = useMemo(
    () => templates.length > 0 && selectedIds.length === templates.length,
    [templates.length, selectedIds.length]
  );

  const someSelected = useMemo(
    () => selectedIds.length > 0 && selectedIds.length < templates.length,
    [selectedIds.length, templates.length]
  );

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(templates.map((t) => t.id));
    }
  }, [allSelected, templates, onSelectionChange]);

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

  if (templates.length === 0) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-12 text-center">
        <Calendar className="w-12 h-12 text-slate-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">
          No templates found
        </h3>
        <p className="text-slate-400">
          Create a new rotation template to get started.
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
                  label="Name"
                  field="name"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="text-left py-3 px-4 text-slate-400">
                <SortHeader
                  label="Activity Type"
                  field="activity_type"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">
                Abbreviation
              </th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">
                Max Residents
              </th>
              <th className="text-left py-3 px-4 text-slate-400 font-medium">
                Supervision
              </th>
              <th className="text-left py-3 px-4 text-slate-400">
                <SortHeader
                  label="Created"
                  field="created_at"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="text-right py-3 px-4 text-slate-400 font-medium">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {templates.map((template) => {
              const isSelected = selectedIds.includes(template.id);

              return (
                <tr
                  key={template.id}
                  className={`
                    border-b border-slate-700/50 transition-colors
                    ${isSelected ? 'bg-violet-500/10' : 'hover:bg-slate-800/50'}
                  `}
                >
                  <td className="py-3 px-4">
                    <RowCheckbox
                      checked={isSelected}
                      onChange={() => handleSelectRow(template.id)}
                      ariaLabel={`Select ${template.name}`}
                    />
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {template.background_color && (
                        <span
                          className="w-3 h-3 rounded"
                          style={{ backgroundColor: template.background_color }}
                        />
                      )}
                      <span className="text-white font-medium">
                        {template.name}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <ActivityTypeBadge
                      activityType={template.activity_type as ActivityType}
                    />
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {template.display_abbreviation ||
                      template.abbreviation ||
                      '-'}
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {template.max_residents ?? '-'}
                  </td>
                  <td className="py-3 px-4">
                    {template.supervision_required ? (
                      <span className="text-emerald-400">Required</span>
                    ) : (
                      <span className="text-slate-500">Not Required</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-slate-400">
                    {new Date(template.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-1">
                      {onView && (
                        <button
                          onClick={() => onView(template)}
                          className="p-1.5 text-slate-400 hover:text-white transition-colors"
                          title="View details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      )}
                      {onEdit && (
                        <button
                          onClick={() => onEdit(template)}
                          className="p-1.5 text-slate-400 hover:text-white transition-colors"
                          title="Edit template"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      )}
                      {onEditPatterns && (
                        <button
                          onClick={() => onEditPatterns(template)}
                          className="p-1.5 text-slate-400 hover:text-blue-400 transition-colors"
                          title="Edit patterns"
                        >
                          <Calendar className="w-4 h-4" />
                        </button>
                      )}
                      {onEditPreferences && (
                        <button
                          onClick={() => onEditPreferences(template)}
                          className="p-1.5 text-slate-400 hover:text-violet-400 transition-colors"
                          title="Edit preferences"
                        >
                          <Settings className="w-4 h-4" />
                        </button>
                      )}
                      {onDelete && (
                        <button
                          onClick={() => onDelete(template)}
                          className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
                          title="Delete template"
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
          {selectedIds.length} template{selectedIds.length !== 1 ? 's' : ''}{' '}
          selected
        </div>
      )}
    </div>
  );
}

export default TemplateTable;
