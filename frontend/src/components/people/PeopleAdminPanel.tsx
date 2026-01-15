'use client';

/**
 * PeopleAdminPanel Component
 *
 * Admin panel for managing people with tier-based access controls.
 * - Tier 1: Role/PGY updates (coordinators)
 * - Tier 2: Bulk delete operations (admins only)
 *
 * Reuses existing admin components for consistency:
 * - PeopleTable for sortable, selectable table view
 * - PeopleBulkActionsToolbar for bulk operations
 * - AddPersonModal for creating new people
 * - EditPersonModal for individual edits
 *
 * WCAG 2.1 AA Compliance: Proper focus management, keyboard navigation,
 * and screen reader support for all interactive elements.
 */
import { useState, useMemo, useCallback, useRef } from 'react';
import {
  Plus,
  Search,
  Filter,
  RefreshCw,
  X,
  Keyboard,
} from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { PeopleTable } from '@/components/admin/PeopleTable';
import { PeopleBulkActionsToolbar } from '@/components/admin/PeopleBulkActionsToolbar';
import { AddPersonModal } from '@/components/AddPersonModal';
import { EditPersonModal } from '@/components/EditPersonModal';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import {
  usePeople,
  useBulkDeletePeople,
  useBulkUpdatePeople,
  type PersonType,
  type PeopleFilters,
} from '@/hooks/usePeople';
import { useDebounce } from '@/hooks/useDebounce';
import { useKeyboardShortcuts, getShortcutDisplay } from '@/hooks/useKeyboardShortcuts';
import { useToast } from '@/contexts/ToastContext';
import type { Person, PersonUpdate } from '@/types/api';
import type { RiskTier } from '@/components/ui/RiskBar';

// ============================================================================
// Types
// ============================================================================

type SortField = 'name' | 'type' | 'pgyLevel' | 'email';
type SortDirection = 'asc' | 'desc';
type BulkActionType = 'delete' | 'update_pgy' | 'update_type';

interface AdminFilters {
  type: PersonType | '';
  pgyLevel: number | '';
  search: string;
}

interface AdminSort {
  field: SortField;
  direction: SortDirection;
}

export interface PeopleAdminPanelProps {
  /** Whether the user can perform bulk delete (Tier 2) */
  canBulkDelete: boolean;
  /** Current risk tier for the panel (used for display purposes) */
  riskTier: RiskTier;
}

// Note: riskTier is passed for potential future use (display indicators, analytics)
// Currently tier restrictions are enforced via canBulkDelete prop

// ============================================================================
// Main Component
// ============================================================================

export function PeopleAdminPanel({
  canBulkDelete,
  riskTier: _riskTier, // Prefixed to indicate intentionally unused (future use)
}: PeopleAdminPanelProps) {
  // Refs
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Toast notifications
  const { toast } = useToast();

  // State
  const [filters, setFilters] = useState<AdminFilters>({
    type: '',
    pgyLevel: '',
    search: '',
  });
  const [sort, setSort] = useState<AdminSort>({
    field: 'name',
    direction: 'asc',
  });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [pendingAction, setPendingAction] = useState<BulkActionType | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingPerson, setEditingPerson] = useState<Person | null>(null);
  const [showShortcutsHint, setShowShortcutsHint] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState<{
    isOpen: boolean;
    count: number;
  }>({ isOpen: false, count: 0 });

  // Debounce search
  const debouncedSearch = useDebounce(filters.search, 300);

  // Build API filters
  const apiFilters: PeopleFilters | undefined = filters.type
    ? { role: filters.type }
    : undefined;

  // Queries
  const {
    data: peopleData,
    isLoading,
    refetch,
  } = usePeople(apiFilters);

  // Mutations
  const bulkDelete = useBulkDeletePeople();
  const bulkUpdate = useBulkUpdatePeople();

  // Client-side filtering
  const people = useMemo(() => {
    if (!peopleData?.items) return [];

    let filtered = [...peopleData.items];

    // Search filter
    if (debouncedSearch) {
      const searchLower = debouncedSearch.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(searchLower) ||
          p.email?.toLowerCase().includes(searchLower)
      );
    }

    // PGY level filter
    if (filters.pgyLevel !== '') {
      filtered = filtered.filter((p) => p.pgyLevel === filters.pgyLevel);
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sort.field) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'type':
          comparison = (a.type || '').localeCompare(b.type || '');
          break;
        case 'pgyLevel':
          comparison = (a.pgyLevel || 0) - (b.pgyLevel || 0);
          break;
        case 'email':
          comparison = (a.email || '').localeCompare(b.email || '');
          break;
      }
      return sort.direction === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [peopleData?.items, debouncedSearch, filters.pgyLevel, sort]);

  // Handlers
  const handleSortChange = useCallback((field: SortField) => {
    setSort((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const handleRefresh = useCallback(() => {
    refetch();
    toast.info('Refreshing people...');
  }, [refetch, toast]);

  const handleFocusSearch = useCallback(() => {
    searchInputRef.current?.focus();
    searchInputRef.current?.select();
  }, []);

  const handleBulkDeleteClick = useCallback(() => {
    setDeleteConfirmation({ isOpen: true, count: selectedIds.length });
  }, [selectedIds.length]);

  const handleBulkDeleteConfirm = useCallback(async () => {
    setDeleteConfirmation({ isOpen: false, count: 0 });
    setPendingAction('delete');
    try {
      await bulkDelete.mutateAsync(selectedIds);
      toast.success(`${selectedIds.length} people deleted`);
      setSelectedIds([]);
    } catch (error) {
      toast.error(error);
    } finally {
      setPendingAction(null);
    }
  }, [selectedIds, bulkDelete, toast]);

  const handleBulkUpdatePGY = useCallback(
    async (pgyLevel: number) => {
      setPendingAction('update_pgy');
      try {
        await bulkUpdate.mutateAsync({
          personIds: selectedIds,
          updates: { pgyLevel } as PersonUpdate,
        });
        toast.success(`${selectedIds.length} people updated to PGY-${pgyLevel}`);
        setSelectedIds([]);
      } catch (error) {
        toast.error(error);
      } finally {
        setPendingAction(null);
      }
    },
    [selectedIds, bulkUpdate, toast]
  );

  const handleBulkUpdateType = useCallback(
    async (type: PersonType) => {
      setPendingAction('update_type');
      try {
        await bulkUpdate.mutateAsync({
          personIds: selectedIds,
          updates: { type } as PersonUpdate,
        });
        toast.success(`${selectedIds.length} people updated to ${type}`);
        setSelectedIds([]);
      } catch (error) {
        toast.error(error);
      } finally {
        setPendingAction(null);
      }
    },
    [selectedIds, bulkUpdate, toast]
  );

  // Note: Row click handling is available through PeopleTable's onSelectionChange
  // Individual person editing is triggered via selection and then edit button

  // Keyboard shortcuts
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: 'k',
        modifiers: ['cmd'],
        handler: handleFocusSearch,
        description: 'Focus search',
      },
      {
        key: 'r',
        handler: handleRefresh,
        description: 'Refresh people',
        ignoreInputs: true,
      },
      {
        key: 'Escape',
        handler: () => {
          if (filters.search) {
            setFilters((prev) => ({ ...prev, search: '' }));
          } else if (selectedIds.length > 0) {
            setSelectedIds([]);
          }
        },
        description: 'Clear selection',
      },
      {
        key: 'n',
        modifiers: ['cmd'],
        handler: () => setShowAddModal(true),
        description: 'Add new person',
      },
      {
        key: '?',
        modifiers: ['shift'],
        handler: () => setShowShortcutsHint((prev) => !prev),
        description: 'Toggle shortcuts help',
        ignoreInputs: true,
      },
    ],
    enabled: true,
  });

  const isPending = pendingAction !== null || bulkDelete.isPending || bulkUpdate.isPending;

  return (
    <div className="space-y-6">
      {/* Filters and Actions Bar */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500"
            aria-hidden="true"
          />
          <input
            ref={searchInputRef}
            type="search"
            placeholder={`Search people... (${getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })})`}
            value={filters.search}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, search: e.target.value }))
            }
            className="w-full pl-10 pr-10 py-2 bg-white dark:bg-slate-800/50 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Search people"
          />
          {filters.search && (
            <button
              onClick={() => setFilters((prev) => ({ ...prev, search: '' }))}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Type Filter */}
        <div className="flex items-center gap-2">
          <Filter
            className="w-4 h-4 text-slate-400 dark:text-slate-500"
            aria-hidden="true"
          />
          <select
            value={filters.type}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                type: e.target.value as PersonType | '',
                pgyLevel: e.target.value === 'faculty' ? '' : prev.pgyLevel,
              }))
            }
            className="px-3 py-2 bg-white dark:bg-slate-800/50 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Filter by type"
          >
            <option value="">All Types</option>
            <option value="resident">Residents</option>
            <option value="faculty">Faculty</option>
          </select>
        </div>

        {/* PGY Level Filter */}
        {(filters.type === '' || filters.type === 'resident') && (
          <select
            value={filters.pgyLevel}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                pgyLevel: e.target.value ? Number(e.target.value) : '',
              }))
            }
            className="px-3 py-2 bg-white dark:bg-slate-800/50 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Filter by PGY level"
          >
            <option value="">All PGY Levels</option>
            {[1, 2, 3, 4, 5].map((level) => (
              <option key={level} value={level}>
                PGY-{level}
              </option>
            ))}
          </select>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Stats */}
        <div className="text-sm text-slate-600 dark:text-slate-400">
          {people.length} {people.length === 1 ? 'person' : 'people'}
          {peopleData?.total && peopleData.total !== people.length && (
            <span> of {peopleData.total}</span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowShortcutsHint((prev) => !prev)}
            className="p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg"
            title="Keyboard shortcuts (Shift+?)"
            aria-label="Show keyboard shortcuts"
          >
            <Keyboard className="w-5 h-5" />
          </button>
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-white transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg"
            title={`Refresh (${getShortcutDisplay({ key: 'r' })})`}
            aria-label="Refresh people list"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900"
          >
            <Plus className="w-4 h-4" />
            Add Person
          </button>
        </div>
      </div>

      {/* Keyboard Shortcuts Hint */}
      {showShortcutsHint && (
        <div
          className="fixed bottom-20 right-4 z-50 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl p-4 max-w-xs"
          role="dialog"
          aria-label="Keyboard shortcuts"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <Keyboard className="w-4 h-4" />
              Keyboard Shortcuts
            </h3>
            <button
              onClick={() => setShowShortcutsHint(false)}
              className="text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              aria-label="Close shortcuts help"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-600 dark:text-slate-300">Focus search</dt>
              <dd>
                <kbd className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-xs">
                  {getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })}
                </kbd>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600 dark:text-slate-300">Add person</dt>
              <dd>
                <kbd className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-xs">
                  {getShortcutDisplay({ key: 'n', modifiers: ['cmd'] })}
                </kbd>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600 dark:text-slate-300">Refresh</dt>
              <dd>
                <kbd className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-xs">R</kbd>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600 dark:text-slate-300">Clear selection</dt>
              <dd>
                <kbd className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-xs">Esc</kbd>
              </dd>
            </div>
          </dl>
        </div>
      )}

      {/* People Table */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="bg-white dark:bg-transparent rounded-lg overflow-hidden">
          <PeopleTable
            people={people}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            sort={sort}
            onSortChange={handleSortChange}
          />
        </div>
      )}

      {/* Bulk Actions Toolbar */}
      <PeopleBulkActionsToolbar
        selectedCount={selectedIds.length}
        onClearSelection={() => setSelectedIds([])}
        onBulkDelete={canBulkDelete ? handleBulkDeleteClick : () => {}}
        onBulkUpdatePGY={handleBulkUpdatePGY}
        onBulkUpdateType={handleBulkUpdateType}
        isPending={isPending}
        pendingAction={pendingAction}
      />

      {/* Tier indicator for non-admin users without bulk delete */}
      {!canBulkDelete && selectedIds.length > 0 && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-30">
          <p className="text-sm text-slate-600 dark:text-slate-400 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-2 shadow-lg">
            Bulk delete requires admin permissions
          </p>
        </div>
      )}

      {/* Add Person Modal */}
      <AddPersonModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
      />

      {/* Edit Person Modal */}
      <EditPersonModal
        isOpen={editingPerson !== null}
        onClose={() => setEditingPerson(null)}
        person={editingPerson}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirmation.isOpen}
        onClose={() => setDeleteConfirmation({ isOpen: false, count: 0 })}
        onConfirm={handleBulkDeleteConfirm}
        title="Delete People"
        message={`Are you sure you want to delete ${deleteConfirmation.count} ${deleteConfirmation.count === 1 ? 'person' : 'people'}? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        isLoading={bulkDelete.isPending}
      />
    </div>
  );
}
