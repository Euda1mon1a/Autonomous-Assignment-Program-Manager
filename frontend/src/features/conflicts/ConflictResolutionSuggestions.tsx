'use client';

import { useState } from 'react';
import {
  Lightbulb,
  Star,
  ArrowRight,
  AlertTriangle,
  Check,
  Loader2,
  ThumbsUp,
  Info,
  User,
  Repeat,
  Trash2,
  Plus,
  Edit3,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useResolutionSuggestions, useApplyResolution } from './hooks';
import type { Conflict, ResolutionChange } from './types';

// ============================================================================
// Props
// ============================================================================

interface ConflictResolutionSuggestionsProps {
  conflict: Conflict;
  onResolved?: (conflict: Conflict) => void;
  onClose?: () => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

function getMethodIcon(method: string) {
  switch (method) {
    case 'swap':
      return Repeat;
    case 'manual_reassign':
      return User;
    case 'cancel_assignment':
      return Trash2;
    case 'add_coverage':
      return Plus;
    case 'auto_resolved':
      return Star;
    default:
      return Edit3;
  }
}

function getMethodLabel(method: string): string {
  const labels: Record<string, string> = {
    auto_resolved: 'Auto-resolve',
    manual_reassign: 'Reassign',
    manual_override: 'Override',
    swap: 'Swap Assignments',
    cancel_assignment: 'Cancel Assignment',
    add_coverage: 'Add Coverage',
    ignored: 'Ignore',
  };
  return labels[method] || method;
}

function getChangeIcon(type: string) {
  switch (type) {
    case 'reassign':
      return ArrowRight;
    case 'remove':
      return Trash2;
    case 'add':
      return Plus;
    case 'swap':
      return Repeat;
    case 'modify':
      return Edit3;
    default:
      return Edit3;
  }
}

function getImpactColor(score: number): string {
  if (score < 30) return 'text-green-600 bg-green-100';
  if (score < 60) return 'text-amber-600 bg-amber-100';
  return 'text-red-600 bg-red-100';
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 80) return 'text-green-600';
  if (confidence >= 50) return 'text-amber-600';
  return 'text-red-600';
}

// ============================================================================
// Component
// ============================================================================

export function ConflictResolutionSuggestions({
  conflict,
  onResolved,
  onClose,
}: ConflictResolutionSuggestionsProps) {
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);
  const [expandedSuggestion, setExpandedSuggestion] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  // Queries
  const {
    data: suggestions,
    isLoading,
    error,
  } = useResolutionSuggestions(conflict.id);

  const applyResolution = useApplyResolution();

  // Handlers
  const handleApply = async () => {
    if (!selectedSuggestion) return;

    try {
      const result = await applyResolution.mutateAsync({
        conflictId: conflict.id,
        suggestionId: selectedSuggestion,
        notes: resolutionNotes || undefined,
      });

      if (onResolved) {
        onResolved(result);
      }
    } catch (_err) {
      // Error handled by mutation
    }
  };

  const handleToggleExpand = (id: string) => {
    setExpandedSuggestion(expandedSuggestion === id ? null : id);
  };

  // Render loading state
  if (isLoading) {
    return (
      <div className="p-6 animate-fadeIn">
        <div className="space-y-4">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            <span className="ml-3 text-gray-600 animate-pulse">Analyzing conflict and generating suggestions...</span>
          </div>
          {/* Loading skeleton for suggestions */}
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="p-4 bg-gray-100 rounded-lg border border-gray-200">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-gray-200 rounded-full"></div>
                  <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-5 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-4 bg-gray-200 rounded w-full"></div>
                    <div className="flex gap-2 mt-2">
                      <div className="h-6 bg-gray-200 rounded w-16"></div>
                      <div className="h-6 bg-gray-200 rounded w-16"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="p-6">
        <div className="flex flex-col items-center justify-center py-12 text-red-500">
          <AlertTriangle className="w-12 h-12 mb-4" />
          <p className="text-lg font-medium">Error loading suggestions</p>
          <p className="text-sm">{error.message}</p>
        </div>
      </div>
    );
  }

  // Render no suggestions
  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="p-6">
        <div className="flex flex-col items-center justify-center py-12 text-gray-500">
          <Info className="w-12 h-12 mb-4" />
          <p className="text-lg font-medium">No automatic suggestions available</p>
          <p className="text-sm text-center mt-2">
            This conflict requires manual resolution. Please review the conflict details
            and resolve it manually or create an override.
          </p>
        </div>
      </div>
    );
  }

  // Sort suggestions by recommendation and confidence
  const sortedSuggestions = [...suggestions].sort((a, b) => {
    if (a.recommended && !b.recommended) return -1;
    if (!a.recommended && b.recommended) return 1;
    return b.confidence - a.confidence;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b bg-gradient-to-r from-amber-50 to-yellow-50" role="region" aria-label="Resolution suggestions header">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-100 rounded-lg" aria-hidden="true">
            <Lightbulb className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Resolution Suggestions</h3>
            <p className="text-sm text-gray-600">
              {suggestions.length} suggestion{suggestions.length !== 1 ? 's' : ''} available
            </p>
          </div>
        </div>
      </div>

      {/* Suggestions list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" role="region" aria-label="Available resolution suggestions" aria-live="polite">
        {sortedSuggestions.map((suggestion, index) => {
          const isSelected = selectedSuggestion === suggestion.id;
          const isExpanded = expandedSuggestion === suggestion.id;
          const MethodIcon = getMethodIcon(suggestion.method);

          return (
            <div
              key={suggestion.id}
              className={`
                rounded-lg border-2 overflow-hidden transition-all duration-300 cursor-pointer animate-fadeInUp
                ${isSelected
                  ? 'border-blue-500 bg-blue-50 shadow-lg scale-[1.02]'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
                }
                ${suggestion.recommended ? 'ring-2 ring-amber-200' : ''}
              `}
              style={{ animationDelay: `${index * 100}ms` }}
              onClick={() => setSelectedSuggestion(suggestion.id)}
              role="option"
              aria-selected={isSelected}
              aria-label={`${suggestion.title} - ${suggestion.recommended ? 'Recommended' : ''} ${suggestion.method}`}
            >
              {/* Suggestion header */}
              <div className="p-4">
                <div className="flex items-start gap-3">
                  {/* Selection indicator */}
                  <div className={`
                    flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center
                    ${isSelected ? 'bg-blue-500 border-blue-500' : 'border-gray-300'}
                  `} aria-hidden="true">
                    {isSelected && <Check className="w-4 h-4 text-white" />}
                  </div>

                  {/* Method icon */}
                  <div className={`
                    flex-shrink-0 p-2 rounded-lg
                    ${isSelected ? 'bg-blue-100' : 'bg-gray-100'}
                  `}>
                    <MethodIcon className={`w-5 h-5 ${isSelected ? 'text-blue-600' : 'text-gray-600'}`} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <h4 className="font-medium text-gray-900">{suggestion.title}</h4>
                      {suggestion.recommended && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">
                          <Star className="w-3 h-3" />
                          Recommended
                        </span>
                      )}
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                        {getMethodLabel(suggestion.method)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{suggestion.description}</p>

                    {/* Metrics */}
                    <div className="flex items-center gap-4 mt-3">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs text-gray-500">Impact:</span>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded ${getImpactColor(suggestion.impactScore)}`}>
                          {suggestion.impactScore < 30 ? 'Low' : suggestion.impactScore < 60 ? 'Medium' : 'High'}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs text-gray-500">Confidence:</span>
                        <span className={`text-xs font-medium ${getConfidenceColor(suggestion.confidence)}`}>
                          {suggestion.confidence}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Expand toggle */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleExpand(suggestion.id);
                    }}
                    className="flex-shrink-0 p-1.5 rounded-md hover:bg-gray-100"
                    aria-label={isExpanded ? 'Collapse' : 'Expand'}
                  >
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-500" />
                    )}
                  </button>
                </div>
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div className="px-4 pb-4 pt-0 animate-slideDown">
                  <div className="border-t pt-4 mt-2">
                    {/* Changes */}
                    <div className="mb-4">
                      <h5 className="text-sm font-medium text-gray-700 mb-2">
                        Proposed Changes ({suggestion.changes.length})
                      </h5>
                      <div className="space-y-2">
                        {suggestion.changes.map((change, index) => (
                          <ChangeItem key={index} change={change} />
                        ))}
                      </div>
                    </div>

                    {/* Side effects */}
                    {suggestion.sideEffects.length > 0 && (
                      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                          <div>
                            <h5 className="text-sm font-medium text-amber-800 mb-1">
                              Potential Side Effects
                            </h5>
                            <ul className="text-sm text-amber-700 space-y-1">
                              {suggestion.sideEffects.map((effect, index) => (
                                <li key={index}>&bull; {effect}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer with action */}
      <div className="p-4 border-t bg-gray-50">
        {selectedSuggestion && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resolution Notes (optional)
            </label>
            <textarea
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Add any notes about this resolution..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={2}
            />
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <ThumbsUp className="w-4 h-4" />
            <span>Suggestions are based on schedule analysis and past resolutions</span>
          </div>

          <div className="flex items-center gap-2">
            {onClose && (
              <button
                onClick={onClose}
                aria-label="Cancel resolution"
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleApply}
              disabled={!selectedSuggestion || applyResolution.isPending}
              aria-label={applyResolution.isPending ? 'Applying resolution' : 'Apply selected resolution'}
              className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-lg active:scale-95"
            >
              {applyResolution.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  Applying...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" aria-hidden="true" />
                  Apply Resolution
                </>
              )}
            </button>
          </div>
        </div>

        {applyResolution.isError && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700" role="alert" aria-live="assertive">
            <strong>Error:</strong> {applyResolution.error?.message || 'Failed to apply resolution'}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Change Item Component
// ============================================================================

interface ChangeItemProps {
  change: ResolutionChange;
}

function ChangeItem({ change }: ChangeItemProps) {
  const ChangeIcon = getChangeIcon(change.type);

  return (
    <div className="flex items-start gap-3 p-2 bg-white border border-gray-200 rounded-lg">
      <div className="flex-shrink-0 p-1.5 bg-gray-100 rounded">
        <ChangeIcon className="w-4 h-4 text-gray-600" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-900">{change.description}</p>
        {change.fromPersonName && change.toPersonName && (
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
            <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded">
              {change.fromPersonName}
            </span>
            <ArrowRight className="w-3 h-3" />
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">
              {change.toPersonName}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
