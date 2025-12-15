'use client';

/**
 * Progress indicator component for import operations
 */

import { CheckCircle, XCircle, AlertTriangle, Loader2 } from 'lucide-react';
import type { ImportProgress } from './types';

// ============================================================================
// Types
// ============================================================================

interface ImportProgressIndicatorProps {
  progress: ImportProgress;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function ImportProgressIndicator({
  progress,
  className = '',
}: ImportProgressIndicatorProps) {
  const percentage = progress.totalRows > 0
    ? Math.round((progress.processedRows / progress.totalRows) * 100)
    : 0;

  // Status icon
  const StatusIcon = () => {
    switch (progress.status) {
      case 'complete':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'parsing':
      case 'validating':
      case 'importing':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return null;
    }
  };

  // Status text color
  const statusTextColor = () => {
    switch (progress.status) {
      case 'complete':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'parsing':
      case 'validating':
      case 'importing':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  // Progress bar color
  const progressBarColor = () => {
    switch (progress.status) {
      case 'complete':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-blue-500';
    }
  };

  if (progress.status === 'idle') {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusIcon />
          <span className={`font-medium ${statusTextColor()}`}>
            {progress.message}
          </span>
        </div>
        {progress.totalRows > 0 && (
          <span className="text-sm text-gray-500">
            {percentage}%
          </span>
        )}
      </div>

      {/* Progress Bar */}
      {(progress.status === 'importing' || progress.status === 'validating' || progress.status === 'parsing') && (
        <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${progressBarColor()}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}

      {/* Statistics */}
      {(progress.status === 'importing' || progress.status === 'complete') && (
        <div className="flex gap-4 text-sm">
          {progress.successCount > 0 && (
            <div className="flex items-center gap-1 text-green-600">
              <CheckCircle className="w-4 h-4" />
              <span>{progress.successCount} successful</span>
            </div>
          )}
          {progress.warningCount > 0 && (
            <div className="flex items-center gap-1 text-yellow-600">
              <AlertTriangle className="w-4 h-4" />
              <span>{progress.warningCount} warnings</span>
            </div>
          )}
          {progress.errorCount > 0 && (
            <div className="flex items-center gap-1 text-red-600">
              <XCircle className="w-4 h-4" />
              <span>{progress.errorCount} errors</span>
            </div>
          )}
        </div>
      )}

      {/* Row Progress */}
      {progress.status === 'importing' && progress.totalRows > 0 && (
        <div className="text-sm text-gray-500">
          Processing row {progress.currentRow} of {progress.totalRows}
        </div>
      )}

      {/* Error Details */}
      {progress.status === 'error' && progress.errors.length > 0 && (
        <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm font-medium text-red-800 mb-2">
            Errors encountered:
          </p>
          <ul className="text-sm text-red-700 list-disc list-inside max-h-32 overflow-y-auto">
            {progress.errors.slice(0, 10).map((error, index) => (
              <li key={index}>
                Row {error.row}: {error.message}
              </li>
            ))}
            {progress.errors.length > 10 && (
              <li className="text-red-600 font-medium">
                ...and {progress.errors.length - 10} more errors
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Skeleton Component
// ============================================================================

export function ImportProgressSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-gray-200 rounded-full" />
          <div className="h-4 w-32 bg-gray-200 rounded" />
        </div>
        <div className="h-4 w-10 bg-gray-200 rounded" />
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5" />
      <div className="flex gap-4">
        <div className="h-4 w-24 bg-gray-200 rounded" />
        <div className="h-4 w-24 bg-gray-200 rounded" />
      </div>
    </div>
  );
}
