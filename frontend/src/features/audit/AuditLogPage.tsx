'use client';

/**
 * AuditLogPage Component
 *
 * Main audit log viewer page that integrates all audit components:
 * - Table view with sorting and pagination
 * - Timeline view
 * - Filtering and search
 * - Export functionality
 * - Change comparison view
 */

import { useState, useCallback, useMemo } from 'react';
import {
  RefreshCw,
  FileText,
  AlertTriangle,
  Table,
  Clock,
  ArrowLeftRight,
  Shield,
} from 'lucide-react';
import { AuditLogTable } from './AuditLogTable';
import { AuditLogFilters } from './AuditLogFilters';
import { AuditLogExport } from './AuditLogExport';
import { AuditTimeline } from './AuditTimeline';
import { ChangeComparison } from './ChangeComparison';
import { useAuditLogs, useAuditStatistics, useAuditUsers } from './hooks';
import type {
  AuditLogEntry,
  AuditLogFilters as AuditFilters,
  AuditLogSort,
  AuditViewMode,
  ComparisonSelection,
  AuditExportConfig,
} from './types';
import { DEFAULT_PAGE_SIZE, DEFAULT_SORT } from './types';

// ============================================================================
// Types
// ============================================================================

interface AuditLogPageProps {
  initialFilters?: AuditFilters;
  initialView?: AuditViewMode;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * View mode toggle buttons
 */
function ViewModeToggle({
  viewMode,
  onViewModeChange,
}: {
  viewMode: AuditViewMode;
  onViewModeChange: (mode: AuditViewMode) => void;
}) {
  const modes: Array<{ mode: AuditViewMode; icon: React.ReactNode; label: string }> = [
    { mode: 'table', icon: <Table className="w-4 h-4" aria-hidden="true" />, label: 'Table' },
    { mode: 'timeline', icon: <Clock className="w-4 h-4" aria-hidden="true" />, label: 'Timeline' },
    { mode: 'comparison', icon: <ArrowLeftRight className="w-4 h-4" aria-hidden="true" />, label: 'Compare' },
  ];

  return (
    <div className="flex items-center bg-gray-100 rounded-lg p-1" role="tablist" aria-label="Audit log view modes">
      {modes.map(({ mode, icon, label }) => (
        <button
          key={mode}
          type="button"
          onClick={() => onViewModeChange(mode)}
          className={`
            flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors
            ${
              viewMode === mode
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }
          `}
          role="tab"
          aria-selected={viewMode === mode}
          aria-label={`${label} view`}
        >
          {icon}
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  );
}

/**
 * Statistics dashboard cards
 */
function StatisticsCards({
  totalEntries,
  acgmeOverrideCount,
  uniqueUsers,
  isLoading,
}: {
  totalEntries: number;
  acgmeOverrideCount: number;
  uniqueUsers: number;
  isLoading: boolean;
}) {
  const stats = [
    {
      label: 'Total Entries',
      value: totalEntries,
      icon: <FileText className="w-5 h-5" aria-hidden="true" />,
      color: 'text-blue-600 bg-blue-100',
    },
    {
      label: 'ACGME Overrides',
      value: acgmeOverrideCount,
      icon: <AlertTriangle className="w-5 h-5" aria-hidden="true" />,
      color: 'text-orange-600 bg-orange-100',
    },
    {
      label: 'Active Users',
      value: uniqueUsers,
      icon: <Shield className="w-5 h-5" aria-hidden="true" />,
      color: 'text-green-600 bg-green-100',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-white rounded-lg shadow p-4 flex items-center gap-4"
          role="status"
          aria-label={`${stat.label}: ${stat.value.toLocaleString()}`}
        >
          <div className={`p-3 rounded-lg ${stat.color}`}>{stat.icon}</div>
          <div>
            <div className="text-sm text-gray-500">{stat.label}</div>
            {isLoading ? (
              <div className="h-7 w-16 bg-gray-200 rounded animate-pulse" />
            ) : (
              <div className="text-2xl font-bold text-gray-900">
                {stat.value.toLocaleString()}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Comparison mode helper panel
 */
function ComparisonModePanel({
  selection,
  onClearSelection,
}: {
  selection: ComparisonSelection;
  onClearSelection: () => void;
}) {
  const hasSelection = selection.before || selection.after;

  if (!hasSelection) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4" role="status" aria-live="polite">
        <div className="flex items-center gap-2 text-blue-700">
          <ArrowLeftRight className="w-5 h-5" aria-hidden="true" />
          <span className="font-medium">Comparison Mode</span>
        </div>
        <p className="text-sm text-blue-600 mt-1">
          Select two entries from the table below to compare their changes side by side.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4" role="status" aria-live="polite">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-blue-700">
          <ArrowLeftRight className="w-5 h-5" aria-hidden="true" />
          <span className="font-medium">
            {selection.before && selection.after
              ? 'Ready to compare'
              : 'Select one more entry'}
          </span>
        </div>
        <button
          type="button"
          onClick={onClearSelection}
          className="text-sm text-blue-600 hover:text-blue-800"
          aria-label="Clear comparison selection"
        >
          Clear selection
        </button>
      </div>
      <div className="flex items-center gap-4 mt-2 text-sm text-blue-600">
        <span>
          Before: {selection.before ? selection.before.entityName || selection.before.id : 'Not selected'}
        </span>
        <span>→</span>
        <span>
          After: {selection.after ? selection.after.entityName || selection.after.id : 'Not selected'}
        </span>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function AuditLogPage({
  initialFilters,
  initialView = 'table',
}: AuditLogPageProps) {
  // State
  const [viewMode, setViewMode] = useState<AuditViewMode>(initialView);
  const [filters, setFilters] = useState<AuditFilters>(initialFilters || {});
  const [sort, setSort] = useState<AuditLogSort>(DEFAULT_SORT);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | undefined>();
  const [comparisonSelection, setComparisonSelection] = useState<ComparisonSelection>({});

  // Queries
  const {
    data: auditData,
    isLoading: isLoadingLogs,
    refetch,
  } = useAuditLogs({
    filters,
    sort,
    pagination: { page, pageSize },
  });

  const { data: statistics, isLoading: isLoadingStats } = useAuditStatistics(
    filters.dateRange
  );

  const { data: users } = useAuditUsers();

  // Derived state
  const logs = auditData?.items || [];
  const totalCount = auditData?.total || 0;

  // Handlers
  const handleFiltersChange = useCallback((newFilters: AuditFilters) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page on filter change
    setSelectedEntry(undefined);
  }, []);

  const handleSortChange = useCallback((newSort: AuditLogSort) => {
    setSort(newSort);
    setPage(1);
  }, []);

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
    setSelectedEntry(undefined);
  }, []);

  const handlePageSizeChange = useCallback((newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1);
    setSelectedEntry(undefined);
  }, []);

  const handleEntrySelect = useCallback(
    (entry: AuditLogEntry) => {
      if (viewMode === 'comparison') {
        // In comparison mode, build the selection
        setComparisonSelection((prev) => {
          if (!prev.before) {
            return { before: entry };
          }
          if (!prev.after && prev.before.id !== entry.id) {
            return { ...prev, after: entry };
          }
          // Start over
          return { before: entry };
        });
      } else {
        setSelectedEntry(entry);
      }
    },
    [viewMode]
  );

  const handleClearComparison = useCallback(() => {
    setComparisonSelection({});
  }, []);

  const handleCloseDetails = useCallback(() => {
    setSelectedEntry(undefined);
  }, []);

  const handleExportAll = useCallback(
    async (config: AuditExportConfig): Promise<Blob> => {
      // This would call the API to export all matching records
      // For now, return a placeholder
      const response = await fetch('/api/audit/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...config, filters }),
      });
      return response.blob();
    },
    [filters]
  );

  // Memoized users list for filters
  const usersList = useMemo(
    () => users?.map((u) => ({ id: u.id, name: u.name })) || [],
    [users]
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Page header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
              <p className="text-gray-600 mt-1">
                Track and review all system changes and user activities
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => refetch()}
                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                disabled={isLoadingLogs}
                aria-label={isLoadingLogs ? 'Refreshing audit logs' : 'Refresh audit logs'}
              >
                <RefreshCw
                  className={`w-4 h-4 ${isLoadingLogs ? 'animate-spin' : ''}`}
                  aria-hidden="true"
                />
                Refresh
              </button>
              <AuditLogExport
                logs={logs}
                filters={filters}
                totalCount={totalCount}
                onExportAll={handleExportAll}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Statistics */}
        <StatisticsCards
          totalEntries={statistics?.totalEntries || totalCount}
          acgmeOverrideCount={statistics?.acgmeOverrideCount || 0}
          uniqueUsers={statistics?.uniqueUsers || 0}
          isLoading={isLoadingStats}
        />

        {/* Filters */}
        <AuditLogFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          users={usersList}
          isLoading={isLoadingLogs}
        />

        {/* View mode toggle */}
        <div className="flex items-center justify-between mt-6 mb-4">
          <ViewModeToggle viewMode={viewMode} onViewModeChange={setViewMode} />
          {!isLoadingLogs && (
            <span className="text-sm text-gray-500">
              {totalCount.toLocaleString()} total entries
            </span>
          )}
        </div>

        {/* Comparison mode helper */}
        {viewMode === 'comparison' && (
          <ComparisonModePanel
            selection={comparisonSelection}
            onClearSelection={handleClearComparison}
          />
        )}

        {/* Main view */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Primary content area */}
          <div className={selectedEntry || (viewMode === 'comparison' && comparisonSelection.before) ? 'lg:col-span-2' : 'lg:col-span-3'}>
            {viewMode === 'table' && (
              <AuditLogTable
                logs={logs}
                total={totalCount}
                page={page}
                pageSize={pageSize}
                sort={sort}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
                onSortChange={handleSortChange}
                onEntrySelect={handleEntrySelect}
                selectedEntryId={selectedEntry?.id}
                isLoading={isLoadingLogs}
              />
            )}

            {viewMode === 'timeline' && (
              <AuditTimeline
                events={logs}
                onEventClick={handleEntrySelect}
                selectedEventId={selectedEntry?.id}
                isLoading={isLoadingLogs}
                maxHeight="calc(100vh - 400px)"
              />
            )}

            {viewMode === 'comparison' && (
              <AuditLogTable
                logs={logs}
                total={totalCount}
                page={page}
                pageSize={pageSize}
                sort={sort}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
                onSortChange={handleSortChange}
                onEntrySelect={handleEntrySelect}
                selectedEntryId={
                  comparisonSelection.after?.id ||
                  comparisonSelection.before?.id
                }
                isLoading={isLoadingLogs}
              />
            )}
          </div>

          {/* Side panel for details/comparison */}
          {(selectedEntry || (viewMode === 'comparison' && comparisonSelection.before)) && (
            <div className="lg:col-span-1">
              {viewMode === 'comparison' && comparisonSelection.before ? (
                <ChangeComparison
                  entry={comparisonSelection.before}
                  compareWith={comparisonSelection.after}
                  onClose={handleClearComparison}
                  onClearComparison={handleClearComparison}
                />
              ) : selectedEntry ? (
                <ChangeComparison
                  entry={selectedEntry}
                  onClose={handleCloseDetails}
                />
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
