'use client';

/**
 * Import preview component showing validated data before confirmation
 */

import { useState, useMemo } from 'react';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Filter,
  Search,
} from 'lucide-react';
import type {
  ImportPreviewResult,
  ImportPreviewRow,
  ImportRowStatus,
} from './types';

// ============================================================================
// Types
// ============================================================================

interface ImportPreviewProps {
  preview: ImportPreviewResult;
  maxDisplayRows?: number;
  className?: string;
}

type StatusFilter = 'all' | ImportRowStatus;

// ============================================================================
// Component
// ============================================================================

export function ImportPreview({
  preview,
  maxDisplayRows = 100,
  className = '',
}: ImportPreviewProps) {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Filter and search rows
  const filteredRows = useMemo(() => {
    let rows = preview.rows;

    // Apply status filter
    if (statusFilter !== 'all') {
      rows = rows.filter(row => row.status === statusFilter);
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      rows = rows.filter(row =>
        Object.values(row.data).some(value =>
          String(value ?? '').toLowerCase().includes(query)
        )
      );
    }

    // Apply sorting
    if (sortColumn) {
      rows = [...rows].sort((a, b) => {
        const aVal = String(a.data[sortColumn] ?? '');
        const bVal = String(b.data[sortColumn] ?? '');
        const comparison = aVal.localeCompare(bVal);
        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }

    return rows;
  }, [preview.rows, statusFilter, searchQuery, sortColumn, sortDirection]);

  // Display limited rows
  const displayRows = filteredRows.slice(0, maxDisplayRows);
  const hasMoreRows = filteredRows.length > maxDisplayRows;

  // Toggle row expansion
  const toggleRowExpansion = (rowNumber: number) => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      if (next.has(rowNumber)) {
        next.delete(rowNumber);
      } else {
        next.add(rowNumber);
      }
      return next;
    });
  };

  // Handle column sort
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  // Status icon component
  const StatusIcon = ({ status }: { status: ImportRowStatus }) => {
    switch (status) {
      case 'valid':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'skipped':
        return <span className="w-4 h-4 text-gray-400">-</span>;
    }
  };

  // Row status background
  const getRowBackground = (status: ImportRowStatus) => {
    switch (status) {
      case 'valid':
        return 'bg-green-50 hover:bg-green-100';
      case 'error':
        return 'bg-red-50 hover:bg-red-100';
      case 'warning':
        return 'bg-yellow-50 hover:bg-yellow-100';
      case 'skipped':
        return 'bg-gray-50 hover:bg-gray-100';
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Summary */}
      <div className="flex flex-wrap gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Total:</span>
          <span className="font-semibold">{preview.totalRows}</span>
        </div>
        <div className="flex items-center gap-2 text-green-600">
          <CheckCircle className="w-4 h-4" />
          <span className="text-sm">Valid: {preview.validRows}</span>
        </div>
        <div className="flex items-center gap-2 text-yellow-600">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-sm">Warnings: {preview.warningRows}</span>
        </div>
        <div className="flex items-center gap-2 text-red-600">
          <XCircle className="w-4 h-4" />
          <span className="text-sm">Errors: {preview.errorRows}</span>
        </div>
        <div className="flex items-center gap-2 text-gray-500">
          <span className="text-sm">Skipped: {preview.skippedRows}</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Rows</option>
            <option value="valid">Valid Only</option>
            <option value="warning">Warnings</option>
            <option value="error">Errors</option>
            <option value="skipped">Skipped</option>
          </select>
        </div>

        {/* Search */}
        <div className="flex-1 min-w-[200px] max-w-xs relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-2 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search data..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Results count */}
        <span className="text-sm text-gray-500">
          Showing {displayRows.length} of {filteredRows.length} rows
        </span>
      </div>

      {/* Data Table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-gray-600 w-16">
                  Status
                </th>
                <th className="px-3 py-2 text-left font-medium text-gray-600 w-12">
                  Row
                </th>
                {preview.columns.map((column) => (
                  <th
                    key={column}
                    className="px-3 py-2 text-left font-medium text-gray-600 cursor-pointer hover:bg-gray-200"
                    onClick={() => handleSort(column)}
                  >
                    <div className="flex items-center gap-1">
                      <span>{column}</span>
                      {sortColumn === column && (
                        sortDirection === 'asc'
                          ? <ChevronUp className="w-3 h-3" />
                          : <ChevronDown className="w-3 h-3" />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {displayRows.map((row) => (
                <PreviewRow
                  key={row.rowNumber}
                  row={row}
                  columns={preview.columns}
                  isExpanded={expandedRows.has(row.rowNumber)}
                  onToggle={() => toggleRowExpansion(row.rowNumber)}
                  StatusIcon={StatusIcon}
                  getRowBackground={getRowBackground}
                />
              ))}
            </tbody>
          </table>
        </div>

        {/* More rows indicator */}
        {hasMoreRows && (
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 text-center text-sm text-gray-600">
            Showing first {maxDisplayRows} rows. {filteredRows.length - maxDisplayRows} more rows not displayed.
          </div>
        )}

        {/* Empty state */}
        {displayRows.length === 0 && (
          <div className="px-4 py-8 text-center text-gray-500">
            No rows match the current filter.
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Preview Row Sub-Component
// ============================================================================

interface PreviewRowProps {
  row: ImportPreviewRow;
  columns: string[];
  isExpanded: boolean;
  onToggle: () => void;
  StatusIcon: React.ComponentType<{ status: ImportRowStatus }>;
  getRowBackground: (status: ImportRowStatus) => string;
}

function PreviewRow({
  row,
  columns,
  isExpanded,
  onToggle,
  StatusIcon,
  getRowBackground,
}: PreviewRowProps) {
  const hasDetails = row.errors.length > 0 || row.warnings.length > 0;

  return (
    <>
      <tr
        className={`${getRowBackground(row.status)} ${hasDetails ? 'cursor-pointer' : ''}`}
        onClick={hasDetails ? onToggle : undefined}
      >
        <td className="px-3 py-2">
          <div className="flex items-center gap-1">
            <StatusIcon status={row.status} />
            {hasDetails && (
              isExpanded
                ? <ChevronUp className="w-3 h-3 text-gray-400" />
                : <ChevronDown className="w-3 h-3 text-gray-400" />
            )}
          </div>
        </td>
        <td className="px-3 py-2 text-gray-500">{row.rowNumber}</td>
        {columns.map((column) => (
          <td key={column} className="px-3 py-2 truncate max-w-xs">
            {formatCellValue(row.data[column])}
          </td>
        ))}
      </tr>
      {isExpanded && hasDetails && (
        <tr className={getRowBackground(row.status)}>
          <td colSpan={columns.length + 2} className="px-3 py-2">
            <div className="pl-6 space-y-2">
              {row.errors.map((error, index) => (
                <div key={`error-${index}`} className="flex items-start gap-2 text-red-700">
                  <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>
                    <strong>{error.column}:</strong> {error.message}
                  </span>
                </div>
              ))}
              {row.warnings.map((warning, index) => (
                <div key={`warning-${index}`} className="flex items-start gap-2 text-yellow-700">
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>
                    <strong>{warning.column}:</strong> {warning.message}
                  </span>
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '-';
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  return String(value);
}

// ============================================================================
// Skeleton Component
// ============================================================================

export function ImportPreviewSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Summary skeleton */}
      <div className="flex gap-4 p-4 bg-gray-50 rounded-lg">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-5 w-20 bg-gray-200 rounded" />
        ))}
      </div>

      {/* Filters skeleton */}
      <div className="flex gap-3 items-center">
        <div className="h-8 w-32 bg-gray-200 rounded" />
        <div className="h-8 w-48 bg-gray-200 rounded" />
      </div>

      {/* Table skeleton */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-100 px-3 py-2 flex gap-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-4 w-20 bg-gray-200 rounded" />
          ))}
        </div>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="px-3 py-3 flex gap-4 border-t border-gray-200">
            {[1, 2, 3, 4, 5].map((j) => (
              <div key={j} className="h-4 w-20 bg-gray-200 rounded" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
