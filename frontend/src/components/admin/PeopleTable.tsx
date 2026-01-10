'use client';

/**
 * PeopleTable Component
 *
 * Displays people (residents and faculty) in a sortable table with row selection
 * for bulk operations. Follows the dark theme pattern from admin pages.
 */
import React from 'react';
import {
  ChevronUp,
  ChevronDown,
  User,
  GraduationCap,
} from 'lucide-react';
import type { Person } from '@/types/api';

// ============================================================================
// Types
// ============================================================================

type SortField = 'name' | 'type' | 'pgyLevel' | 'email';
type SortDirection = 'asc' | 'desc';

export interface PeopleTableProps {
  /** List of people to display */
  people: Person[];
  /** Currently selected person IDs */
  selectedIds: string[];
  /** Callback when selection changes */
  onSelectionChange: (ids: string[]) => void;
  /** Current sort configuration */
  sort: { field: SortField; direction: SortDirection };
  /** Callback when sort changes */
  onSortChange: (field: SortField) => void;
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
              ? 'text-cyan-400'
              : 'text-slate-600'
          }`}
        />
        <ChevronDown
          className={`w-3 h-3 ${
            isActive && currentSort.direction === 'desc'
              ? 'text-cyan-400'
              : 'text-slate-600'
          }`}
        />
      </span>
    </button>
  );
}

interface TypeBadgeProps {
  type: string | undefined;
}

function TypeBadge({ type }: TypeBadgeProps) {
  const isResident = type === 'resident';
  const isFaculty = type === 'faculty';

  return (
    <span
      className={`
        inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium
        ${isResident ? 'bg-blue-500/20 text-blue-400' : ''}
        ${isFaculty ? 'bg-purple-500/20 text-purple-400' : ''}
        ${!isResident && !isFaculty ? 'bg-slate-500/20 text-slate-400' : ''}
      `}
    >
      {isResident && <GraduationCap className="w-3 h-3" />}
      {isFaculty && <User className="w-3 h-3" />}
      {type || 'Unknown'}
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
      className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0 cursor-pointer"
    />
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function PeopleTable({
  people,
  selectedIds,
  onSelectionChange,
  sort,
  onSortChange,
}: PeopleTableProps) {
  // Selection handlers
  const isAllSelected = people.length > 0 && selectedIds.length === people.length;
  const isSomeSelected = selectedIds.length > 0 && selectedIds.length < people.length;

  const handleSelectAll = () => {
    if (isAllSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(people.map((p) => p.id));
    }
  };

  const handleSelectRow = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((sid) => sid !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  if (people.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <User className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">No people found</p>
        <p className="text-sm">Try adjusting your filters or add new people.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="px-4 py-3 text-left w-10">
                <RowCheckbox
                  checked={isAllSelected}
                  indeterminate={isSomeSelected}
                  onChange={handleSelectAll}
                  ariaLabel={isAllSelected ? 'Deselect all' : 'Select all'}
                />
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
                <SortHeader
                  label="Name"
                  field="name"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
                <SortHeader
                  label="Type"
                  field="type"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
                <SortHeader
                  label="PGY Level"
                  field="pgyLevel"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
                <SortHeader
                  label="Email"
                  field="email"
                  currentSort={sort}
                  onSort={onSortChange}
                />
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
                Specialties
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {people.map((person) => {
              const isSelected = selectedIds.includes(person.id);

              return (
                <tr
                  key={person.id}
                  className={`
                    transition-colors cursor-pointer
                    ${isSelected ? 'bg-cyan-500/10' : 'hover:bg-slate-700/30'}
                  `}
                  onClick={() => handleSelectRow(person.id)}
                >
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <RowCheckbox
                      checked={isSelected}
                      onChange={() => handleSelectRow(person.id)}
                      ariaLabel={`Select ${person.name}`}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-white">{person.name}</div>
                  </td>
                  <td className="px-4 py-3">
                    <TypeBadge type={person.type} />
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {person.type === 'resident' && person.pgyLevel ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/20 text-emerald-400">
                        PGY-{person.pgyLevel}
                      </span>
                    ) : (
                      <span className="text-slate-500">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {person.email || <span className="text-slate-500">-</span>}
                  </td>
                  <td className="px-4 py-3">
                    {person.specialties && person.specialties.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {person.specialties.slice(0, 2).map((specialty, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded text-xs bg-slate-600/50 text-slate-300"
                          >
                            {specialty}
                          </span>
                        ))}
                        {person.specialties.length > 2 && (
                          <span className="px-2 py-0.5 rounded text-xs bg-slate-600/50 text-slate-400">
                            +{person.specialties.length - 2}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-500">-</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
