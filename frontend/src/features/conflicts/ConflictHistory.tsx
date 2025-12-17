'use client';

import { useState } from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import {
  History,
  Clock,
  User,
  AlertTriangle,
  Check,
  X,
  Eye,
  Shield,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Calendar,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { useConflictHistory, useConflictPatterns } from './hooks';
import type { Conflict, ConflictHistoryEntry, ConflictPattern, ConflictType } from './types';
import { getTypeLabel } from './ConflictCard';

// ============================================================================
// Props
// ============================================================================

interface ConflictHistoryProps {
  conflict?: Conflict;
  showPatterns?: boolean;
}

interface ConflictHistoryTimelineProps {
  conflictId: string;
}

interface ConflictPatternsViewProps {
  onPatternSelect?: (pattern: ConflictPattern) => void;
}

// ============================================================================
// History Action Icons
// ============================================================================

function getActionIcon(action: ConflictHistoryEntry['action']) {
  switch (action) {
    case 'detected':
      return AlertTriangle;
    case 'updated':
      return RefreshCw;
    case 'resolved':
      return Check;
    case 'reopened':
      return Eye;
    case 'ignored':
      return X;
    case 'overridden':
      return Shield;
    default:
      return History;
  }
}

function getActionColor(action: ConflictHistoryEntry['action']): {
  bg: string;
  icon: string;
  text: string;
} {
  switch (action) {
    case 'detected':
      return {
        bg: 'bg-red-100',
        icon: 'text-red-500',
        text: 'text-red-700',
      };
    case 'resolved':
      return {
        bg: 'bg-green-100',
        icon: 'text-green-500',
        text: 'text-green-700',
      };
    case 'ignored':
      return {
        bg: 'bg-gray-100',
        icon: 'text-gray-500',
        text: 'text-gray-700',
      };
    case 'overridden':
      return {
        bg: 'bg-amber-100',
        icon: 'text-amber-500',
        text: 'text-amber-700',
      };
    case 'reopened':
      return {
        bg: 'bg-orange-100',
        icon: 'text-orange-500',
        text: 'text-orange-700',
      };
    case 'updated':
    default:
      return {
        bg: 'bg-blue-100',
        icon: 'text-blue-500',
        text: 'text-blue-700',
      };
  }
}

function getActionLabel(action: ConflictHistoryEntry['action']): string {
  const labels: Record<ConflictHistoryEntry['action'], string> = {
    detected: 'Conflict Detected',
    updated: 'Updated',
    resolved: 'Resolved',
    reopened: 'Reopened',
    ignored: 'Ignored',
    overridden: 'Override Created',
  };
  return labels[action] || action;
}

// ============================================================================
// Conflict History Timeline Component
// ============================================================================

export function ConflictHistoryTimeline({ conflictId }: ConflictHistoryTimelineProps) {
  const { data: history, isLoading, error } = useConflictHistory(conflictId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
        Failed to load history: {error.message}
      </div>
    );
  }

  if (!history || history.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <History className="w-10 h-10 mx-auto mb-2 text-gray-400" />
        <p>No history available</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-4 top-6 bottom-6 w-0.5 bg-gray-200" />

      {/* Timeline items */}
      <div className="space-y-6">
        {history.map((entry, index) => {
          const ActionIcon = getActionIcon(entry.action);
          const colors = getActionColor(entry.action);

          return (
            <div
              key={entry.id}
              className="relative flex gap-4 animate-fadeInUp"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Timeline dot */}
              <div className={`
                flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center z-10 transition-transform duration-300 hover:scale-110
                ${colors.bg}
              `}>
                <ActionIcon className={`w-4 h-4 ${colors.icon}`} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 pb-2">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className={`font-medium ${colors.text}`}>
                    {getActionLabel(entry.action)}
                  </span>
                  {entry.user_name && (
                    <span className="text-sm text-gray-500 flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {entry.user_name}
                    </span>
                  )}
                </div>

                <p className="text-sm text-gray-500 flex items-center gap-1 mb-2">
                  <Clock className="w-3 h-3" />
                  {format(new Date(entry.timestamp), 'MMM d, yyyy h:mm a')}
                  <span className="text-gray-400 ml-1">
                    ({formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })})
                  </span>
                </p>

                {/* Changes */}
                {Object.keys(entry.changes).length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-3 text-sm">
                    <p className="font-medium text-gray-700 mb-2">Changes:</p>
                    <ul className="space-y-1">
                      {Object.entries(entry.changes).map(([field, change]) => (
                        <li key={field} className="text-gray-600">
                          <span className="font-mono text-xs bg-gray-200 px-1 rounded">
                            {field}
                          </span>
                          : <span className="text-red-600 line-through">{String(change.from)}</span>
                          {' → '}
                          <span className="text-green-600">{String(change.to)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Notes */}
                {entry.notes && (
                  <p className="mt-2 text-sm text-gray-600 italic">
                    &ldquo;{entry.notes}&rdquo;
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// Conflict Patterns View Component
// ============================================================================

export function ConflictPatternsView({ onPatternSelect }: ConflictPatternsViewProps) {
  const [selectedType, setSelectedType] = useState<ConflictType | null>(null);
  const { data: patterns, isLoading, error } = useConflictPatterns();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        Failed to load patterns: {error.message}
      </div>
    );
  }

  if (!patterns || patterns.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <BarChart3 className="w-12 h-12 mx-auto mb-3 text-gray-400" />
        <p className="text-lg font-medium">No patterns detected</p>
        <p className="text-sm">
          Patterns will appear here once enough conflict data is collected.
        </p>
      </div>
    );
  }

  // Filter patterns by type if selected
  const filteredPatterns = selectedType
    ? patterns.filter((p) => p.type === selectedType)
    : patterns;

  // Get unique types for filter
  const uniqueTypes = Array.from(new Set(patterns.map((p) => p.type)));

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-600 font-medium">Total Patterns</p>
          <p className="text-2xl font-bold text-blue-900">{patterns.length}</p>
        </div>
        <div className="p-4 bg-amber-50 rounded-lg">
          <p className="text-sm text-amber-600 font-medium">Most Frequent</p>
          <p className="text-lg font-bold text-amber-900">
            {patterns.length > 0
              ? getTypeLabel(patterns.sort((a, b) => b.frequency - a.frequency)[0].type)
              : '-'}
          </p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <p className="text-sm text-green-600 font-medium">People Affected</p>
          <p className="text-2xl font-bold text-green-900">
            {patterns.reduce((acc, p) => acc + p.affected_people.length, 0)}
          </p>
        </div>
      </div>

      {/* Type filter */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm text-gray-500">Filter by type:</span>
        <button
          onClick={() => setSelectedType(null)}
          className={`
            px-3 py-1 rounded-full text-sm transition-colors
            ${!selectedType ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
          `}
        >
          All
        </button>
        {uniqueTypes.map((type) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            className={`
              px-3 py-1 rounded-full text-sm transition-colors
              ${selectedType === type ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
            `}
          >
            {getTypeLabel(type)}
          </button>
        ))}
      </div>

      {/* Patterns list */}
      <div className="space-y-4">
        {filteredPatterns.map((pattern) => (
          <PatternCard
            key={pattern.id}
            pattern={pattern}
            onClick={() => onPatternSelect?.(pattern)}
          />
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Pattern Card Component
// ============================================================================

interface PatternCardProps {
  pattern: ConflictPattern;
  onClick?: () => void;
}

function PatternCard({ pattern, onClick }: PatternCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Determine trend (simplified - in production, compare with previous period)
  const isIncreasing = pattern.frequency > 5;

  return (
    <div
      className="border rounded-lg overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer hover:-translate-y-0.5 animate-fadeInUp"
      onClick={onClick}
    >
      <div className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-full">
                {getTypeLabel(pattern.type)}
              </span>
              <span className={`
                flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
                ${isIncreasing ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}
              `}>
                {isIncreasing ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                {isIncreasing ? 'Increasing' : 'Stable'}
              </span>
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
              <span className="flex items-center gap-1">
                <BarChart3 className="w-4 h-4" />
                {pattern.frequency} occurrences
              </span>
              <span className="flex items-center gap-1">
                <User className="w-4 h-4" />
                {pattern.affected_people.length} people
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                Last: {format(new Date(pattern.last_occurrence), 'MMM d')}
              </span>
            </div>

            {pattern.root_cause && (
              <div className="mb-3">
                <p className="text-sm font-medium text-gray-700">Potential Root Cause:</p>
                <p className="text-sm text-gray-600">{pattern.root_cause}</p>
              </div>
            )}

            {pattern.suggested_prevention && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm font-medium text-green-800 mb-1">Suggested Prevention:</p>
                <p className="text-sm text-green-700">{pattern.suggested_prevention}</p>
              </div>
            )}
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronRight
              className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            />
          </button>
        </div>
      </div>

      {/* Expanded view - affected people */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0">
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Most Affected People</h4>
            <div className="space-y-2">
              {pattern.affected_people
                .sort((a, b) => b.occurrence_count - a.occurrence_count)
                .slice(0, 5)
                .map((person) => (
                  <div
                    key={person.id}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-gray-500" />
                      </div>
                      <span className="text-sm font-medium text-gray-900">{person.name}</span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {person.occurrence_count} occurrence{person.occurrence_count !== 1 ? 's' : ''}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Conflict History Component
// ============================================================================

export function ConflictHistory({ conflict, showPatterns = true }: ConflictHistoryProps) {
  const [activeTab, setActiveTab] = useState<'history' | 'patterns'>(
    conflict ? 'history' : 'patterns'
  );

  return (
    <div className="h-full flex flex-col">
      {/* Tab header */}
      <div className="border-b">
        <div className="flex gap-4 px-4">
          {conflict && (
            <button
              onClick={() => setActiveTab('history')}
              className={`
                py-3 px-1 border-b-2 text-sm font-medium transition-colors
                ${activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
                }
              `}
            >
              <History className="w-4 h-4 inline mr-2" />
              History
            </button>
          )}
          {showPatterns && (
            <button
              onClick={() => setActiveTab('patterns')}
              className={`
                py-3 px-1 border-b-2 text-sm font-medium transition-colors
                ${activeTab === 'patterns'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
                }
              `}
            >
              <BarChart3 className="w-4 h-4 inline mr-2" />
              Patterns
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'history' && conflict ? (
          <ConflictHistoryTimeline conflictId={conflict.id} />
        ) : (
          <ConflictPatternsView />
        )}
      </div>
    </div>
  );
}
