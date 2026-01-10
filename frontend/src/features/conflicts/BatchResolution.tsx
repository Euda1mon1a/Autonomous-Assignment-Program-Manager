'use client';

import { useState, useMemo, useCallback } from 'react';
import { format } from 'date-fns';
import {
  CheckSquare,
  Square,
  AlertTriangle,
  Check,
  X,
  Loader2,
  Play,
  Pause,
  RotateCcw,
  Filter,
  ChevronDown,
  AlertOctagon,
  AlertCircle,
  Info,
  Users,
} from 'lucide-react';
import { useBatchResolve, useBatchIgnore } from './hooks';
import type {
  Conflict,
  ConflictSeverity,
  ConflictType,
  ResolutionMethod,
  BatchResolutionResult,
} from './types';
import { getSeverityStyles, getTypeLabel } from './ConflictCard';

// ============================================================================
// Props
// ============================================================================

interface BatchResolutionProps {
  conflicts: Conflict[];
  onComplete?: () => void;
  onCancel?: () => void;
}

interface BatchResolutionResultsProps {
  results: BatchResolutionResult;
  onClose: () => void;
  onRetryFailed?: () => void;
}

// ============================================================================
// Resolution Method Options
// ============================================================================

const RESOLUTION_METHODS: { value: ResolutionMethod; label: string; description: string }[] = [
  {
    value: 'auto_resolved',
    label: 'Auto-resolve',
    description: 'Apply system-recommended resolutions automatically',
  },
  {
    value: 'ignored',
    label: 'Ignore All',
    description: 'Ignore all selected conflicts (requires reason)',
  },
];

// ============================================================================
// Severity Priority
// ============================================================================

const SEVERITY_ORDER: Record<ConflictSeverity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

// ============================================================================
// Component
// ============================================================================

export function BatchResolution({
  conflicts,
  onComplete,
  onCancel,
}: BatchResolutionProps) {
  // State
  const [selectedIds, setSelectedIds] = useState<Set<string>>(
    new Set(conflicts.map((c) => c.id))
  );
  const [method, setMethod] = useState<ResolutionMethod>('auto_resolved');
  const [ignoreReason, setIgnoreReason] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [results, setResults] = useState<BatchResolutionResult | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<ConflictSeverity | null>(null);
  const [filterType, setFilterType] = useState<ConflictType | null>(null);

  // Mutations
  const batchResolve = useBatchResolve();
  const batchIgnore = useBatchIgnore();

  // Computed values
  const filteredConflicts = useMemo(() => {
    return conflicts.filter((c) => {
      if (filterSeverity && c.severity !== filterSeverity) return false;
      if (filterType && c.type !== filterType) return false;
      return true;
    });
  }, [conflicts, filterSeverity, filterType]);

  const selectedConflicts = useMemo(() => {
    return filteredConflicts.filter((c) => selectedIds.has(c.id));
  }, [filteredConflicts, selectedIds]);

  const groupedBySeverity = useMemo(() => {
    const groups: Record<ConflictSeverity, Conflict[]> = {
      critical: [],
      high: [],
      medium: [],
      low: [],
    };
    selectedConflicts.forEach((c) => {
      groups[c.severity].push(c);
    });
    return groups;
  }, [selectedConflicts]);

  const hasCritical = groupedBySeverity.critical.length > 0;
  const uniqueTypes = useMemo(
    () => Array.from(new Set(conflicts.map((c) => c.type))),
    [conflicts]
  );

  // Handlers
  const handleToggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (selectedIds.size === filteredConflicts.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredConflicts.map((c) => c.id)));
    }
  }, [filteredConflicts, selectedIds.size]);

  const handleSelectBySeverity = useCallback((severity: ConflictSeverity) => {
    const ids = filteredConflicts
      .filter((c) => c.severity === severity)
      .map((c) => c.id);
    setSelectedIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => next.add(id));
      return next;
    });
  }, [filteredConflicts]);

  const handleProcess = useCallback(async () => {
    if (selectedIds.size === 0) return;

    setIsProcessing(true);
    setIsPaused(false);

    try {
      if (method === 'ignored') {
        const result = await batchIgnore.mutateAsync({
          conflictIds: Array.from(selectedIds),
          reason: ignoreReason,
        });
        setResults({
          total: selectedIds.size,
          successful: result.success,
          failed: result.failed,
          results: [],
        });
      } else {
        const result = await batchResolve.mutateAsync({
          conflictIds: Array.from(selectedIds),
          resolutionMethod: method,
        });
        setResults(result);
      }
    } catch (err) {
      // Error handled by mutations
    } finally {
      setIsProcessing(false);
    }
  }, [selectedIds, method, ignoreReason, batchResolve, batchIgnore]);

  const handleReset = useCallback(() => {
    setResults(null);
    setSelectedIds(new Set(conflicts.map((c) => c.id)));
    setMethod('auto_resolved');
    setIgnoreReason('');
  }, [conflicts]);

  // Validation
  const isValid = method !== 'ignored' || ignoreReason.trim().length > 0;

  // Render results
  if (results) {
    return (
      <BatchResolutionResults
        results={results}
        onClose={() => {
          setResults(null);
          onComplete?.();
        }}
        onRetryFailed={handleReset}
      />
    );
  }

  return (
    <div className="flex flex-col h-full animate-fadeIn">
      {/* Header */}
      <div className="p-4 border-b bg-blue-50 shadow-sm">
        <div className="flex items-center justify-between animate-slideDown">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Batch Resolution</h2>
            <p className="text-sm text-gray-600">
              {selectedIds.size} of {filteredConflicts.length} conflicts selected
            </p>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-blue-100 rounded-lg transition-all duration-200 active:scale-95"
            aria-label="Cancel"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Warning for critical conflicts */}
      {hasCritical && (
        <div className="px-4 py-3 bg-red-50 border-b border-red-200 flex items-start gap-3" role="alert" aria-live="polite">
          <AlertOctagon className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="text-sm">
            <p className="font-medium text-red-800">
              {groupedBySeverity.critical.length} critical conflict{groupedBySeverity.critical.length !== 1 ? 's' : ''} selected
            </p>
            <p className="text-red-700 mt-1">
              Critical conflicts may affect patient safety or regulatory compliance.
              Consider reviewing these individually before batch processing.
            </p>
          </div>
        </div>
      )}

      {/* Filters and selection controls */}
      <div className="p-4 border-b bg-gray-50 space-y-3">
        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <Filter className="w-4 h-4" aria-hidden="true" />
            Filter:
          </span>

          {/* Severity filter */}
          <div className="relative">
            <select
              value={filterSeverity || ''}
              onChange={(e) => setFilterSeverity((e.target.value || null) as ConflictSeverity | null)}
              className="appearance-none pl-3 pr-8 py-1.5 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" aria-hidden="true" />
          </div>

          {/* Type filter */}
          <div className="relative">
            <select
              value={filterType || ''}
              onChange={(e) => setFilterType((e.target.value || null) as ConflictType | null)}
              className="appearance-none pl-3 pr-8 py-1.5 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All types</option>
              {uniqueTypes.map((type) => (
                <option key={type} value={type}>
                  {getTypeLabel(type)}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" aria-hidden="true" />
          </div>
        </div>

        {/* Quick selection buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleSelectAll}
            aria-label={selectedIds.size === filteredConflicts.length ? 'Deselect all conflicts' : 'Select all conflicts'}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            {selectedIds.size === filteredConflicts.length ? (
              <CheckSquare className="w-4 h-4 text-blue-500" aria-hidden="true" />
            ) : (
              <Square className="w-4 h-4 text-gray-400" aria-hidden="true" />
            )}
            Select All
          </button>
          <span className="text-gray-300">|</span>
          {(['critical', 'high', 'medium', 'low'] as ConflictSeverity[]).map((severity) => {
            const count = filteredConflicts.filter((c) => c.severity === severity).length;
            if (count === 0) return null;
            const styles = getSeverityStyles(severity);
            return (
              <button
                key={severity}
                onClick={() => handleSelectBySeverity(severity)}
                aria-label={`Select all ${severity} severity conflicts (${count} total)`}
                className={`
                  flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg border
                  ${styles.bg} ${styles.border} ${styles.text}
                `}
              >
                Select {severity} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Conflict list */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {filteredConflicts
            .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])
            .map((conflict, index) => {
              const styles = getSeverityStyles(conflict.severity);
              const isSelected = selectedIds.has(conflict.id);

              return (
                <div
                  key={conflict.id}
                  className={`
                    flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all duration-200 animate-fadeInUp
                    ${isSelected ? `${styles.bg} ${styles.border} shadow-md` : 'bg-white border-gray-200 hover:shadow-sm'}
                  `}
                  style={{ animationDelay: `${index * 30}ms` }}
                  onClick={() => handleToggleSelect(conflict.id)}
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleSelect(conflict.id);
                    }}
                    aria-label={isSelected ? `Deselect ${conflict.title}` : `Select ${conflict.title}`}
                    className="flex-shrink-0"
                  >
                    {isSelected ? (
                      <CheckSquare className="w-5 h-5 text-blue-500" aria-hidden="true" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400" aria-hidden="true" />
                    )}
                  </button>

                  <div className={`flex-shrink-0 ${styles.icon}`} aria-hidden="true">
                    {conflict.severity === 'critical' ? (
                      <AlertOctagon className="w-5 h-5" />
                    ) : conflict.severity === 'high' ? (
                      <AlertTriangle className="w-5 h-5" />
                    ) : conflict.severity === 'medium' ? (
                      <AlertCircle className="w-5 h-5" />
                    ) : (
                      <Info className="w-5 h-5" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {conflict.title}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span>{getTypeLabel(conflict.type)}</span>
                      <span>{format(new Date(conflict.conflictDate), 'MMM d')}</span>
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" aria-hidden="true" />
                        {conflict.affectedPersonIds.length}
                      </span>
                    </div>
                  </div>

                  <span className={`
                    flex-shrink-0 px-2 py-0.5 rounded-full text-xs font-medium
                    ${styles.badge}
                  `}>
                    {conflict.severity}
                  </span>
                </div>
              );
            })}
        </div>
      </div>

      {/* Resolution options */}
      <div className="p-4 border-t bg-gray-50 space-y-4">
        {/* Method selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Resolution Method
          </label>
          <div className="space-y-2">
            {RESOLUTION_METHODS.map((opt) => (
              <label
                key={opt.value}
                className={`
                  flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors
                  ${method === opt.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <input
                  type="radio"
                  name="method"
                  value={opt.value}
                  checked={method === opt.value}
                  onChange={(e) => setMethod(e.target.value as ResolutionMethod)}
                  className="mt-1"
                />
                <div>
                  <span className="font-medium text-gray-900">{opt.label}</span>
                  <p className="text-sm text-gray-500">{opt.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Ignore reason (if applicable) */}
        {method === 'ignored' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason for Ignoring <span className="text-red-500">*</span>
            </label>
            <textarea
              value={ignoreReason}
              onChange={(e) => setIgnoreReason(e.target.value)}
              placeholder="Provide a reason for ignoring these conflicts..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={2}
              required
            />
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-sm text-gray-500">
            {selectedIds.size} conflict{selectedIds.size !== 1 ? 's' : ''} will be processed
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onCancel}
              aria-label="Cancel batch resolution"
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleProcess}
              disabled={selectedIds.size === 0 || !isValid || isProcessing}
              aria-label={isProcessing ? 'Processing conflicts' : `Process ${selectedIds.size} conflicts`}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-lg active:scale-95"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" aria-hidden="true" />
                  Process {selectedIds.size} Conflicts
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Batch Resolution Results Component
// ============================================================================

function BatchResolutionResults({
  results,
  onClose,
  onRetryFailed,
}: BatchResolutionResultsProps) {
  const successRate = Math.round((results.successful / results.total) * 100);

  return (
    <div className="flex flex-col h-full animate-fadeIn">
      {/* Header */}
      <div className={`
        p-4 border-b shadow-sm animate-slideDown
        ${results.failed === 0 ? 'bg-green-50' : results.successful === 0 ? 'bg-red-50' : 'bg-amber-50'}
      `}>
        <div className="flex items-center gap-3">
          <div className={`
            p-2 rounded-full
            ${results.failed === 0 ? 'bg-green-100' : results.successful === 0 ? 'bg-red-100' : 'bg-amber-100'}
          `} aria-hidden="true">
            {results.failed === 0 ? (
              <Check className="w-6 h-6 text-green-600" />
            ) : results.successful === 0 ? (
              <X className="w-6 h-6 text-red-600" />
            ) : (
              <AlertTriangle className="w-6 h-6 text-amber-600" />
            )}
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {results.failed === 0
                ? 'All Conflicts Resolved'
                : results.successful === 0
                ? 'Resolution Failed'
                : 'Partial Success'}
            </h2>
            <p className="text-sm text-gray-600">
              {results.successful} of {results.total} conflicts resolved ({successRate}%)
            </p>
          </div>
        </div>
      </div>

      {/* Summary stats */}
      <div className="p-4 border-b">
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg text-center">
            <p className="text-2xl font-bold text-gray-900">{results.total}</p>
            <p className="text-sm text-gray-500">Total</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg text-center">
            <p className="text-2xl font-bold text-green-600">{results.successful}</p>
            <p className="text-sm text-green-700">Successful</p>
          </div>
          <div className="p-4 bg-red-50 rounded-lg text-center">
            <p className="text-2xl font-bold text-red-600">{results.failed}</p>
            <p className="text-sm text-red-700">Failed</p>
          </div>
        </div>
      </div>

      {/* Individual results */}
      {results.results.length > 0 && (
        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Resolution Details</h3>
          <div className="space-y-2">
            {results.results.map((result, index) => (
              <div
                key={result.conflictId || index}
                className={`
                  flex items-center gap-3 p-3 rounded-lg border
                  ${result.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}
                `}
                role="listitem"
              >
                {result.success ? (
                  <Check className="w-5 h-5 text-green-500 flex-shrink-0" aria-hidden="true" />
                ) : (
                  <X className="w-5 h-5 text-red-500 flex-shrink-0" aria-hidden="true" />
                )}
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium ${result.success ? 'text-green-800' : 'text-red-800'}`}>
                    {result.message}
                  </p>
                  <p className="text-xs text-gray-500 font-mono truncate">
                    ID: {result.conflictId}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex items-center justify-end gap-2">
          {results.failed > 0 && onRetryFailed && (
            <button
              onClick={onRetryFailed}
              aria-label={`Retry ${results.failed} failed conflicts`}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RotateCcw className="w-4 h-4" aria-hidden="true" />
              Retry Failed
            </button>
          )}
          <button
            onClick={onClose}
            aria-label="Close batch resolution results"
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
