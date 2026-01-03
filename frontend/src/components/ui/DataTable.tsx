/**
 * DataTable Component
 *
 * Sortable, filterable data table with pagination
 */

import React, { useState, useMemo } from 'react';
import { Badge } from './Badge';

export interface Column<T> {
  key: string;
  header: string;
  accessor: (row: T) => string | number | boolean | Date | null | undefined;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: string | number | boolean | Date | null | undefined, row: T) => React.ReactNode;
  width?: string;
}

export interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  pageSize?: number;
  searchable?: boolean;
  className?: string;
}

export function DataTable<T>({
  data,
  columns,
  rowKey,
  onRowClick,
  pageSize = 10,
  searchable = true,
  className = '',
}: DataTableProps<T>) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  // Filter data based on search
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) return data;

    return data.filter(row => {
      return columns.some(column => {
        const value = column.accessor(row);
        return String(value).toLowerCase().includes(searchQuery.toLowerCase());
      });
    });
  }, [data, columns, searchQuery]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortColumn) return filteredData;

    const column = columns.find(c => c.key === sortColumn);
    if (!column) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aVal = column.accessor(a);
      const bVal = column.accessor(b);

      // Handle null/undefined values - put them at the end
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return sortDirection === 'asc' ? 1 : -1;
      if (bVal == null) return sortDirection === 'asc' ? -1 : 1;

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortColumn, sortDirection, columns]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return sortedData.slice(startIndex, startIndex + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  const handleSort = (columnKey: string) => {
    if (sortColumn === columnKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  return (
    <div className={`data-table ${className}`}>
      {/* Search Bar */}
      {searchable && (
        <div className="mb-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1); // Reset to first page on search
            }}
            placeholder="Search..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto bg-white rounded-lg shadow">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {columns.map((column) => {
                const getSortDirection = () => {
                   if (sortColumn !== column.key) return undefined;
                   return sortDirection === 'asc' ? 'ascending' : 'descending';
                };

                return (
                  <th
                    key={column.key}
                    scope="col"
                    aria-sort={getSortDirection()}
                    className={`px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider ${
                      column.width ? `w-${column.width}` : ''
                    }`}
                  >
                    {column.sortable ? (
                      <button
                        onClick={() => handleSort(column.key)}
                        className="flex items-center gap-2 hover:text-gray-900 focus:outline-none focus:underline group"
                      >
                        <span>{column.header}</span>
                        <span className="text-gray-400 group-hover:text-gray-600">
                          {sortColumn === column.key ? (
                            sortDirection === 'asc' ? '↑' : '↓'
                          ) : (
                            '↕'
                          )}
                        </span>
                      </button>
                    ) : (
                      <div className="flex items-center gap-2">
                         <span>{column.header}</span>
                      </div>
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-gray-500"
                >
                  No data to display
                </td>
              </tr>
            ) : (
              paginatedData.map((row) => (
                <tr
                  key={rowKey(row)}
                  className={`${
                    onRowClick
                      ? 'cursor-pointer hover:bg-gray-50 transition-colors'
                      : ''
                  }`}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((column) => {
                    const value = column.accessor(row);
                    // Convert Date to string for display, leave other values as-is
                    const displayValue = value instanceof Date
                      ? value.toLocaleDateString()
                      : value;
                    return (
                      <td
                        key={column.key}
                        className="px-4 py-3 text-sm text-gray-900"
                      >
                        {column.render ? column.render(value, row) : displayValue}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-gray-600">
            Showing {((currentPage - 1) * pageSize) + 1} to{' '}
            {Math.min(currentPage * pageSize, sortedData.length)} of{' '}
            {sortedData.length} results
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Previous
            </button>

            {/* Page Numbers */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    currentPage === pageNum
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataTable;
