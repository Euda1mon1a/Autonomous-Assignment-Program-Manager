'use client';

/**
 * Admin People Page
 *
 * Management interface for people (residents and faculty) with:
 * - Sortable, filterable people list
 * - Multi-select for bulk operations
 * - Filter by type (resident/faculty) and PGY level
 */
import { useState, useCallback, useMemo, useRef } from 'react';
import {
  UserCog,
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
import {
  usePeople,
  useBulkDeletePeople,
  useBulkUpdatePeople,
  type PersonType,
} from '@/hooks/usePeople';
import { useDebounce } from '@/hooks/useDebounce';
import { useKeyboardShortcuts, getShortcutDisplay } from '@/hooks/useKeyboardShortcuts';
import { useToast } from '@/contexts/ToastContext';
import type { PersonUpdate } from '@/types/api';

// ============================================================================
// Types
// ============================================================================

type SortField = 'name' | 'type' | 'pgy_level' | 'email';
type SortDirection = 'asc' | 'desc';

interface PeopleFilters {
  type: PersonType | '';
  pgy_level: number | '';
  search: string;
}

interface PeopleSort {
  field: SortField;
  direction: SortDirection;
}

type BulkActionType = 'delete' | 'update_pgy' | 'update_type';

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminPeoplePage() {
  // Refs for keyboard shortcuts
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [showShortcutsHint, setShowShortcutsHint] = useState(false);

  // Toast notifications
  const { toast } = useToast();

  // State
  const [filters, setFilters] = useState<PeopleFilters>({
    type: '',
    pgy_level: '',
    search: '',
  });
  const [sort, setSort] = useState<PeopleSort>({
    field: 'name',
    direction: 'asc',
  });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [pendingAction, setPendingAction] = useState<BulkActionType | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // Debounce search input for better performance
  const debouncedSearch = useDebounce(filters.search, 300);

  // Queries - pass type filter to backend
  const {
    data: peopleData,
    isLoading: peopleLoading,
    refetch: refetchPeople,
  } = usePeople(
    filters.type ? { role: filters.type } : undefined
  );

  // Mutations
  const bulkDelete = useBulkDeletePeople();
  const bulkUpdate = useBulkUpdatePeople();

  // Derived data - client-side filtering for search and PGY level
  const people = useMemo(() => {
    if (!peopleData?.items) return [];

    let filtered = [...peopleData.items];

    // Search filter - using debounced value
    if (debouncedSearch) {
      const searchLower = debouncedSearch.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(searchLower) ||
          p.email?.toLowerCase().includes(searchLower)
      );
    }

    // PGY level filter (client-side for now)
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
        case 'pgy_level':
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
    refetchPeople();
    toast.info('Refreshing people...');
  }, [refetchPeople, toast]);

  const handleFocusSearch = useCallback(() => {
    searchInputRef.current?.focus();
    searchInputRef.current?.select();
  }, []);

  const handleBulkDelete = useCallback(async () => {
    if (!confirm(`Delete ${selectedIds.length} people? This cannot be undone.`)) {
      return;
    }

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
          updates: { pgy_level: pgyLevel } as PersonUpdate,
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg">
                <UserCog className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">
                  People Management
                </h1>
                <p className="text-sm text-slate-300">
                  Manage residents and faculty
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowShortcutsHint((prev) => !prev)}
                className="p-2 text-slate-300 hover:text-white transition-colors"
                title="Keyboard shortcuts (Shift+?)"
              >
                <Keyboard className="w-5 h-5" />
              </button>
              <button
                onClick={handleRefresh}
                disabled={peopleLoading}
                className="p-2 text-slate-300 hover:text-white transition-colors disabled:opacity-50"
                title={`Refresh (${getShortcutDisplay({ key: 'r' })})`}
              >
                <RefreshCw className={`w-5 h-5 ${peopleLoading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg font-medium transition-all"
              >
                <Plus className="w-4 h-4" />
                Add Person
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Keyboard Shortcuts Hint */}
      {showShortcutsHint && (
        <div className="fixed bottom-4 right-4 z-50 bg-slate-800 border border-slate-700 rounded-lg shadow-xl p-4 max-w-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Keyboard className="w-4 h-4" />
              Keyboard Shortcuts
            </h3>
            <button
              onClick={() => setShowShortcutsHint(false)}
              className="text-slate-300 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-slate-300">
              <span>Focus search</span>
              <kbd className="px-2 py-0.5 bg-slate-700 rounded text-xs">{getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })}</kbd>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Refresh</span>
              <kbd className="px-2 py-0.5 bg-slate-700 rounded text-xs">R</kbd>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Clear selection</span>
              <kbd className="px-2 py-0.5 bg-slate-700 rounded text-xs">Esc</kbd>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>This help</span>
              <kbd className="px-2 py-0.5 bg-slate-700 rounded text-xs">Shift+?</kbd>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder={`Search people... (${getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })})`}
              value={filters.search}
              onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
              className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            />
            {filters.search && (
              <button
                onClick={() => setFilters((prev) => ({ ...prev, search: '' }))}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-300" />
            <select
              value={filters.type}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, type: e.target.value as PersonType | '' }))
              }
              className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            >
              <option value="">All Types</option>
              <option value="resident">Residents</option>
              <option value="faculty">Faculty</option>
            </select>
          </div>

          {/* PGY Level Filter (only show for residents) */}
          {(filters.type === '' || filters.type === 'resident') && (
            <select
              value={filters.pgyLevel}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  pgy_level: e.target.value ? Number(e.target.value) : '',
                }))
              }
              className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            >
              <option value="">All PGY Levels</option>
              {[1, 2, 3, 4, 5].map((level) => (
                <option key={level} value={level}>PGY-{level}</option>
              ))}
            </select>
          )}

          {/* Stats */}
          <div className="flex-1" />
          <div className="text-sm text-slate-300">
            {people.length} {people.length === 1 ? 'person' : 'people'}
            {peopleData?.total && peopleData.total !== people.length && (
              <span> of {peopleData.total}</span>
            )}
          </div>
        </div>

        {/* People Table */}
        {peopleLoading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner />
          </div>
        ) : (
          <PeopleTable
            people={people}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            sort={sort}
            onSortChange={handleSortChange}
          />
        )}
      </main>

      {/* Bulk Actions Toolbar */}
      <PeopleBulkActionsToolbar
        selectedCount={selectedIds.length}
        onClearSelection={() => setSelectedIds([])}
        onBulkDelete={handleBulkDelete}
        onBulkUpdatePGY={handleBulkUpdatePGY}
        onBulkUpdateType={handleBulkUpdateType}
        isPending={isPending}
        pendingAction={pendingAction}
      />

      {/* Add Person Modal */}
      <AddPersonModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
      />
    </div>
  );
}
