'use client';

/**
 * CallAdminTab Component
 *
 * Admin panel for call assignment management (Tier 1/2 users only).
 * Provides functionality for:
 * - Viewing and filtering call assignments
 * - Bulk operations (delete, reassign)
 * - PCAT (Post-Call Availability Tracking) management
 * - Creating new call assignments
 *
 * Access Control:
 * - Tier 1 (Coordinator): Can edit within scope
 * - Tier 2 (Admin): Full access including bulk delete
 *
 * WCAG 2.1 AA compliant with keyboard shortcuts.
 */

import { useState, useCallback, useMemo, useRef } from 'react';
import {
  Search,
  Filter,
  RefreshCw,
  Calendar,
  X,
  Keyboard,
  Plus,
  AlertCircle,
  Shield,
} from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { CallAssignmentTable } from '@/components/admin/CallAssignmentTable';
import { CallBulkActionsToolbar } from '@/components/admin/CallBulkActionsToolbar';
import { CreateCallAssignmentModal } from '@/components/admin/CreateCallAssignmentModal';
import { PCATPreviewModal, createPCATPreviewData } from '@/components/admin/PCATPreviewModal';
import { EquityPreviewPanel } from '@/components/admin/EquityPreviewPanel';
import { useFaculty } from '@/hooks/usePeople';
import { useDebounce } from '@/hooks/useDebounce';
import { useKeyboardShortcuts, getShortcutDisplay } from '@/hooks/useKeyboardShortcuts';
import { useToast } from '@/contexts/ToastContext';
import {
  useCallAssignments,
  useDeleteCallAssignment,
  useBulkDeleteCallAssignments,
  useBulkUpdateCallAssignments,
  useGeneratePCAT,
  useEquityPreview,
} from '@/hooks/useCallAssignments';
import type {
  CallAssignment,
  CallSortField,
  CallFilters,
  CallSort,
  CallBulkActionType,
  CallType,
  DayOfWeek,
} from '@/types/faculty-call';
import { CALL_TYPE_CONFIGS } from '@/types/faculty-call';
import type { CallAssignment as ApiCallAssignment } from '@/types/call-assignment';
import type { RiskTier } from '@/components/ui/RiskBar';

// ============================================================================
// Types
// ============================================================================

interface CallAdminTabProps {
  /** User's permission tier */
  userTier: RiskTier;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Gets the day of week from a date string
 */
function getDayOfWeek(dateStr: string): DayOfWeek {
  const days: DayOfWeek[] = [
    'Sunday',
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
  ];
  const date = new Date(dateStr + 'T00:00:00');
  return days[date.getDay()];
}

/**
 * Maps API call type to UI call type
 */
function mapCallType(apiCallType: string, isWeekend: boolean): CallType {
  if (isWeekend) {
    return 'sunday';
  }
  switch (apiCallType) {
    case 'overnight':
      return 'weekday';
    case 'weekend':
      return 'sunday';
    case 'backup':
      return 'backup';
    default:
      return 'weekday';
  }
}

/**
 * Transforms API response to UI-friendly format
 * Returns null if required fields are missing (defensive against bad data)
 */
function transformApiAssignment(apiAssignment: ApiCallAssignment): CallAssignment | null {
  // Defensive: skip assignments with missing date
  if (!apiAssignment.date) {
    console.warn('Skipping assignment with missing date:', apiAssignment.id);
    return null;
  }

  const dayOfWeek = getDayOfWeek(apiAssignment.date);
  const callType = mapCallType(apiAssignment.callType, apiAssignment.isWeekend);

  return {
    id: apiAssignment.id,
    date: apiAssignment.date,
    dayOfWeek: dayOfWeek,
    personId: apiAssignment.personId,
    personName: apiAssignment.person?.name || 'Unknown',
    callType: callType,
    // Note: postCallStatus is not in API response, default to available
    postCallStatus: 'available',
    notes: null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

function getDefaultDateRange() {
  const today = new Date();
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

  return {
    start: startOfMonth.toISOString().split('T')[0],
    end: endOfMonth.toISOString().split('T')[0],
  };
}

// ============================================================================
// Main Component
// ============================================================================

export function CallAdminTab({ userTier }: CallAdminTabProps) {
  // Refs for keyboard shortcuts
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [showShortcutsHint, setShowShortcutsHint] = useState(false);

  // Toast notifications
  const { toast } = useToast();

  // Default date range
  const defaultDates = getDefaultDateRange();

  // State
  const [filters, setFilters] = useState<CallFilters>({
    startDate: defaultDates.start,
    endDate: defaultDates.end,
    personId: '',
    callType: '',
    search: '',
  });
  const [sort, setSort] = useState<CallSort>({
    field: 'date',
    direction: 'asc',
  });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [pendingAction, setPendingAction] = useState<CallBulkActionType | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPCATPreview, setShowPCATPreview] = useState(false);
  const [showEquityPreview, setShowEquityPreview] = useState(false);
  const [pendingReassignPersonId, setPendingReassignPersonId] = useState<string | null>(null);

  // Debounce search input for better performance
  const debouncedSearch = useDebounce(filters.search, 300);

  // Fetch faculty for reassignment dropdown
  const { data: facultyData } = useFaculty();
  const availableFaculty = useMemo(() => facultyData?.items || [], [facultyData?.items]);

  // Fetch call assignments from API
  const {
    data: apiData,
    isLoading,
    isError,
    error,
    refetch,
  } = useCallAssignments({
    startDate: filters.startDate,
    endDate: filters.endDate,
    personId: filters.personId || undefined,
  });

  // Mutations
  const deleteAssignmentMutation = useDeleteCallAssignment();
  const bulkDeleteMutation = useBulkDeleteCallAssignments();
  const bulkUpdateMutation = useBulkUpdateCallAssignments();
  const generatePCATMutation = useGeneratePCAT();
  const equityPreviewMutation = useEquityPreview();

  // Transform and filter data
  const assignments = useMemo(() => {
    if (!apiData?.items) return [];

    // Transform API data to UI format, filtering out any null results
    let transformed = apiData.items
      .map(transformApiAssignment)
      .filter((a): a is CallAssignment => a !== null);

    // Client-side search filter
    if (debouncedSearch) {
      const searchLower = debouncedSearch.toLowerCase();
      transformed = transformed.filter(
        (a) =>
          a.personName.toLowerCase().includes(searchLower) ||
          a.callType.toLowerCase().includes(searchLower)
      );
    }

    // Client-side call type filter (since API types differ)
    if (filters.callType) {
      transformed = transformed.filter((a) => a.callType === filters.callType);
    }

    // Sort
    transformed.sort((a, b) => {
      let comparison = 0;
      switch (sort.field) {
        case 'date':
          comparison = a.date.localeCompare(b.date);
          break;
        case 'personName':
          comparison = a.personName.localeCompare(b.personName);
          break;
        case 'callType':
          comparison = a.callType.localeCompare(b.callType);
          break;
      }
      return sort.direction === 'asc' ? comparison : -comparison;
    });

    return transformed;
  }, [apiData?.items, debouncedSearch, filters.callType, sort]);

  // PCAT Preview data computation
  const pcatPreviewData = useMemo(() => {
    const selectedAssignments = assignments.filter((a) => selectedIds.includes(a.id));
    return createPCATPreviewData(selectedAssignments);
  }, [assignments, selectedIds]);

  // Get pending reassign person name for equity preview
  const pendingReassignPersonName = useMemo(() => {
    if (!pendingReassignPersonId) return undefined;
    return availableFaculty.find((p) => p.id === pendingReassignPersonId)?.name;
  }, [pendingReassignPersonId, availableFaculty]);

  // Permission checks
  const canBulkDelete = userTier >= 2; // Only Tier 2 (admin)
  const canCreate = userTier >= 1; // Tier 1+ can create

  // Handlers
  const handleSortChange = useCallback((field: CallSortField) => {
    setSort((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const handleRefresh = useCallback(async () => {
    toast.info('Refreshing call assignments...');
    try {
      await refetch();
      toast.success('Call assignments refreshed');
    } catch {
      toast.error('Failed to refresh call assignments');
    }
  }, [toast, refetch]);

  const handleFocusSearch = useCallback(() => {
    searchInputRef.current?.focus();
    searchInputRef.current?.select();
  }, []);

  const handleDeleteSingle = useCallback(
    async (assignment: CallAssignment) => {
      if (confirm(`Delete call assignment for ${assignment.personName} on ${assignment.date}?`)) {
        try {
          await deleteAssignmentMutation.mutateAsync(assignment.id);
          toast.success('Call assignment deleted');
        } catch (err) {
          toast.error(`Failed to delete: ${err instanceof Error ? err.message : 'Unknown error'}`);
        }
      }
    },
    [deleteAssignmentMutation, toast]
  );

  const handleBulkDelete = useCallback(async () => {
    if (!canBulkDelete) {
      toast.error('You do not have permission to perform bulk deletes');
      return;
    }
    setPendingAction('delete');
    try {
      const result = await bulkDeleteMutation.mutateAsync(selectedIds);
      if (result.errors.length > 0) {
        toast.warning(`Deleted ${result.deleted} assignments. ${result.errors.length} failed.`);
      } else {
        toast.success(`${result.deleted} call assignment(s) deleted`);
      }
      setSelectedIds([]);
    } catch (err) {
      toast.error(`Failed to delete: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setPendingAction(null);
    }
  }, [selectedIds, bulkDeleteMutation, toast, canBulkDelete]);

  // Show equity preview before reassignment
  const handleBulkReassignRequest = useCallback(
    async (personId: string) => {
      setPendingReassignPersonId(personId);
      // Fetch equity preview
      try {
        await equityPreviewMutation.mutateAsync({
          startDate: filters.startDate,
          endDate: filters.endDate,
          simulatedChanges: selectedIds.map((assignmentId) => ({
            assignmentId: assignmentId,
            newPersonId: personId,
          })),
        });
        setShowEquityPreview(true);
      } catch (err) {
        toast.error(
          `Failed to load equity preview: ${err instanceof Error ? err.message : 'Unknown error'}`
        );
        setPendingReassignPersonId(null);
      }
    },
    [selectedIds, filters.startDate, filters.endDate, equityPreviewMutation, toast]
  );

  // Execute the actual reassignment after preview confirmation
  const handleConfirmReassign = useCallback(async () => {
    if (!pendingReassignPersonId) return;

    setPendingAction('reassign');
    const person = availableFaculty.find((p) => p.id === pendingReassignPersonId);
    try {
      const result = await bulkUpdateMutation.mutateAsync({
        assignmentIds: selectedIds,
        updates: { personId: pendingReassignPersonId },
      });
      if (result.errors.length > 0) {
        toast.warning(`Reassigned ${result.updated} assignments. ${result.errors.length} failed.`);
      } else {
        toast.success(
          `${result.updated} call assignment(s) reassigned to ${person?.name || 'selected faculty'}`
        );
      }
      setSelectedIds([]);
      setShowEquityPreview(false);
      setPendingReassignPersonId(null);
    } catch (err) {
      toast.error(`Failed to reassign: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setPendingAction(null);
    }
  }, [selectedIds, pendingReassignPersonId, availableFaculty, bulkUpdateMutation, toast]);

  // Show PCAT preview modal instead of immediately applying
  const handleShowPCATPreview = useCallback(() => {
    setShowPCATPreview(true);
  }, []);

  // Execute PCAT after preview confirmation
  const handleConfirmPCAT = useCallback(async () => {
    setPendingAction('apply_pcat');
    try {
      const result = await generatePCATMutation.mutateAsync({
        assignmentIds: selectedIds,
      });
      if (result.errors.length > 0) {
        toast.warning(
          `Processed ${result.processed} assignments. PCAT: ${result.pcatCreated}, DO: ${result.doCreated}. ${result.errors.length} errors.`
        );
      } else {
        toast.success(`PCAT/DO assignments created: ${result.pcatCreated} PCAT, ${result.doCreated} DO`);
      }
      setSelectedIds([]);
      setShowPCATPreview(false);
    } catch (err) {
      toast.error(`Failed to apply PCAT: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setPendingAction(null);
    }
  }, [selectedIds, generatePCATMutation, toast]);

  const handleClearPCAT = useCallback(async () => {
    setPendingAction('clear_pcat');
    // Note: Clear PCAT would need backend support for postCallStatus field
    toast.info('Clear PCAT functionality requires backend enhancement for postCallStatus tracking');
    setPendingAction(null);
  }, [toast]);

  const handleRowClick = useCallback((assignment: CallAssignment) => {
    // Could open detail/edit modal in the future
    console.log('Row clicked:', assignment);
  }, []);

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
        description: 'Refresh assignments',
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
        description: 'Clear selection / search',
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

  const isPending = pendingAction !== null;

  return (
    <div className="space-y-6">
      {/* Tier-specific warning for Tier 2 */}
      {userTier >= 2 && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <Shield className="w-5 h-5 text-red-600 flex-shrink-0" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium text-red-800">Admin Mode Active</p>
            <p className="text-sm text-red-700">
              You have access to bulk operations that can affect multiple records. Use with caution.
            </p>
          </div>
        </div>
      )}

      {/* Actions Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowShortcutsHint((prev) => !prev)}
            className="p-2 text-slate-500 hover:text-slate-700 transition-colors rounded-lg hover:bg-slate-100"
            title="Keyboard shortcuts (Shift+?)"
            aria-label="Show keyboard shortcuts"
          >
            <Keyboard className="w-5 h-5" />
          </button>
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="p-2 text-slate-500 hover:text-slate-700 transition-colors rounded-lg hover:bg-slate-100 disabled:opacity-50"
            title={`Refresh (${getShortcutDisplay({ key: 'r' })})`}
            aria-label="Refresh call assignments"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {canCreate && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <Plus className="w-4 h-4" aria-hidden="true" />
            New Call Assignment
          </button>
        )}
      </div>

      {/* Keyboard Shortcuts Hint */}
      {showShortcutsHint && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Keyboard className="w-4 h-4" aria-hidden="true" />
              Keyboard Shortcuts
            </h3>
            <button
              onClick={() => setShowShortcutsHint(false)}
              className="text-slate-400 hover:text-white"
              aria-label="Close keyboard shortcuts"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex justify-between text-slate-300">
              <span>Focus search</span>
              <kbd className="px-2 py-0.5 bg-slate-700 rounded text-xs">
                {getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })}
              </kbd>
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

      {/* Filters */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Date Range */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-500" aria-hidden="true" />
            <label htmlFor="start-date" className="sr-only">
              Start date
            </label>
            <input
              id="start-date"
              type="date"
              value={filters.startDate}
              onChange={(e) => setFilters((prev) => ({ ...prev, startDate: e.target.value }))}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <span className="text-slate-500">to</span>
            <label htmlFor="end-date" className="sr-only">
              End date
            </label>
            <input
              id="end-date"
              type="date"
              value={filters.endDate}
              onChange={(e) => setFilters((prev) => ({ ...prev, endDate: e.target.value }))}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Person Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" aria-hidden="true" />
            <label htmlFor="person-filter" className="sr-only">
              Filter by faculty
            </label>
            <select
              id="person-filter"
              value={filters.personId}
              onChange={(e) => setFilters((prev) => ({ ...prev, personId: e.target.value }))}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Faculty</option>
              {availableFaculty.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </div>

          {/* Call Type Filter */}
          <div>
            <label htmlFor="calltype-filter" className="sr-only">
              Filter by call type
            </label>
            <select
              id="calltype-filter"
              value={filters.callType}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, callType: e.target.value as CallType | '' }))
              }
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Call Types</option>
              {CALL_TYPE_CONFIGS.map((config) => (
                <option key={config.type} value={config.type}>
                  {config.label}
                </option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
              aria-hidden="true"
            />
            <label htmlFor="search-input" className="sr-only">
              Search assignments
            </label>
            <input
              ref={searchInputRef}
              id="search-input"
              type="text"
              placeholder={`Search... (${getShortcutDisplay({ key: 'k', modifiers: ['cmd'] })})`}
              value={filters.search}
              onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
              className="w-full pl-10 pr-10 py-2 border border-slate-300 rounded-lg text-sm placeholder-slate-400 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {filters.search && (
              <button
                onClick={() => setFilters((prev) => ({ ...prev, search: '' }))}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Stats */}
          <div className="flex-1" />
          <div className="text-sm text-slate-600">
            {assignments.length} assignment{assignments.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {/* Call Assignment Table */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner />
          </div>
        ) : isError ? (
          <div className="p-8 text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" aria-hidden="true" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">
              Failed to load call assignments
            </h3>
            <p className="text-slate-600 mb-4">{error?.message || 'An unexpected error occurred'}</p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : (
          <CallAssignmentTable
            assignments={assignments}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            sort={sort}
            onSortChange={handleSortChange}
            onRowClick={handleRowClick}
            onDelete={handleDeleteSingle}
          />
        )}
      </div>

      {/* Bulk Actions Toolbar */}
      <CallBulkActionsToolbar
        selectedCount={selectedIds.length}
        onClearSelection={() => setSelectedIds([])}
        onBulkDelete={canBulkDelete ? handleBulkDelete : undefined}
        onBulkReassign={handleBulkReassignRequest}
        onApplyPCAT={handleShowPCATPreview}
        onClearPCAT={handleClearPCAT}
        isPending={isPending}
        pendingAction={pendingAction}
        availablePeople={availableFaculty}
      />

      {/* Create Call Assignment Modal */}
      <CreateCallAssignmentModal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} />

      {/* PCAT Preview Modal */}
      <PCATPreviewModal
        isOpen={showPCATPreview}
        onClose={() => setShowPCATPreview(false)}
        onConfirm={handleConfirmPCAT}
        isPending={pendingAction === 'apply_pcat'}
        previewAssignments={pcatPreviewData.previewAssignments}
        pcatCount={pcatPreviewData.pcatCount}
        doCount={pcatPreviewData.doCount}
        skippedCount={pcatPreviewData.skippedCount}
      />

      {/* Equity Preview Panel */}
      <EquityPreviewPanel
        isOpen={showEquityPreview}
        onClose={() => {
          setShowEquityPreview(false);
          setPendingReassignPersonId(null);
        }}
        previewData={equityPreviewMutation.data || null}
        isLoading={equityPreviewMutation.isPending}
        error={equityPreviewMutation.error?.message}
        onConfirm={handleConfirmReassign}
        isConfirmPending={pendingAction === 'reassign'}
        targetPersonName={pendingReassignPersonName}
      />
    </div>
  );
}
