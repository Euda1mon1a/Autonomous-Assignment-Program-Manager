'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import {
  AlertTriangle,
  AlertCircle,
  AlertOctagon,
  Info,
  Calendar,
  User,
  Clock,
  ChevronDown,
  ChevronUp,
  Check,
  X,
  MoreHorizontal,
  Lightbulb,
  History,
  Shield,
} from 'lucide-react';
import type { Conflict, ConflictSeverity, ConflictType, ConflictStatus } from './types';

// ============================================================================
// Props
// ============================================================================

interface ConflictCardProps {
  conflict: Conflict;
  isSelected?: boolean;
  onSelect?: (conflict: Conflict) => void;
  onResolve?: (conflict: Conflict) => void;
  onViewSuggestions?: (conflict: Conflict) => void;
  onViewHistory?: (conflict: Conflict) => void;
  onOverride?: (conflict: Conflict) => void;
  onIgnore?: (conflict: Conflict) => void;
  compact?: boolean;
}

// ============================================================================
// Helper Functions
// ============================================================================

function getSeverityStyles(severity: ConflictSeverity): {
  bg: string;
  border: string;
  text: string;
  icon: string;
  badge: string;
} {
  switch (severity) {
    case 'critical':
      return {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-800',
        icon: 'text-red-500',
        badge: 'bg-red-100 text-red-700',
      };
    case 'high':
      return {
        bg: 'bg-orange-50',
        border: 'border-orange-200',
        text: 'text-orange-800',
        icon: 'text-orange-500',
        badge: 'bg-orange-100 text-orange-700',
      };
    case 'medium':
      return {
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        text: 'text-amber-800',
        icon: 'text-amber-500',
        badge: 'bg-amber-100 text-amber-700',
      };
    case 'low':
      return {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-blue-800',
        icon: 'text-blue-500',
        badge: 'bg-blue-100 text-blue-700',
      };
  }
}

function getSeverityIcon(severity: ConflictSeverity) {
  switch (severity) {
    case 'critical':
      return AlertOctagon;
    case 'high':
      return AlertTriangle;
    case 'medium':
      return AlertCircle;
    case 'low':
      return Info;
  }
}

function getTypeLabel(type: ConflictType): string {
  const labels: Record<ConflictType, string> = {
    scheduling_overlap: 'Scheduling Overlap',
    acgmeViolation: 'ACGME Violation',
    supervision_missing: 'Missing Supervision',
    capacity_exceeded: 'Capacity Exceeded',
    absence_conflict: 'Absence Conflict',
    qualification_mismatch: 'Qualification Mismatch',
    consecutive_duty: 'Consecutive Duty',
    rest_period: 'Rest Period Violation',
    coverage_gap: 'Coverage Gap',
  };
  return labels[type] || type;
}

function getTypeIcon(type: ConflictType) {
  switch (type) {
    case 'scheduling_overlap':
      return Calendar;
    case 'acgmeViolation':
      return Shield;
    case 'supervision_missing':
      return User;
    case 'capacity_exceeded':
      return AlertCircle;
    case 'absence_conflict':
      return Calendar;
    case 'qualification_mismatch':
      return User;
    case 'consecutive_duty':
      return Clock;
    case 'rest_period':
      return Clock;
    case 'coverage_gap':
      return AlertTriangle;
    default:
      return AlertCircle;
  }
}

function getStatusStyles(status: ConflictStatus): {
  bg: string;
  text: string;
  dot: string;
} {
  switch (status) {
    case 'unresolved':
      return {
        bg: 'bg-red-100',
        text: 'text-red-700',
        dot: 'bg-red-500',
      };
    case 'pending_review':
      return {
        bg: 'bg-yellow-100',
        text: 'text-yellow-700',
        dot: 'bg-yellow-500',
      };
    case 'resolved':
      return {
        bg: 'bg-green-100',
        text: 'text-green-700',
        dot: 'bg-green-500',
      };
    case 'ignored':
      return {
        bg: 'bg-gray-100',
        text: 'text-gray-700',
        dot: 'bg-gray-500',
      };
  }
}

function getStatusLabel(status: ConflictStatus): string {
  const labels: Record<ConflictStatus, string> = {
    unresolved: 'Unresolved',
    pending_review: 'Pending Review',
    resolved: 'Resolved',
    ignored: 'Ignored',
  };
  return labels[status] || status;
}

// ============================================================================
// Component
// ============================================================================

export function ConflictCard({
  conflict,
  isSelected = false,
  onSelect,
  onResolve,
  onViewSuggestions,
  onViewHistory,
  onOverride,
  onIgnore,
  compact = false,
}: ConflictCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const severityStyles = getSeverityStyles(conflict.severity);
  const statusStyles = getStatusStyles(conflict.status);
  const SeverityIcon = getSeverityIcon(conflict.severity);
  const TypeIcon = getTypeIcon(conflict.type);

  const handleCardClick = () => {
    if (onSelect) {
      onSelect(conflict);
    }
  };

  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  // Compact view for list displays
  if (compact) {
    return (
      <div
        className={`
          flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all
          ${severityStyles.bg} ${severityStyles.border}
          ${isSelected ? 'ring-2 ring-blue-500' : ''}
          hover:shadow-md
        `}
        onClick={handleCardClick}
        role="button"
        aria-label={`${conflict.title} - ${conflict.severity} severity conflict`}
      >
        <div className={`flex-shrink-0 ${severityStyles.icon}`} aria-hidden="true">
          <SeverityIcon className="w-5 h-5" />
        </div>

        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium truncate ${severityStyles.text}`}>
            {conflict.title}
          </p>
          <p className="text-xs text-gray-500 truncate">
            {format(new Date(conflict.conflictDate), 'MMM d, yyyy')}
            {conflict.conflictSession && ` - ${conflict.conflictSession}`}
          </p>
        </div>

        <div className={`flex-shrink-0 px-2 py-1 rounded-full text-xs font-medium ${statusStyles.bg} ${statusStyles.text}`}>
          {getStatusLabel(conflict.status)}
        </div>
      </div>
    );
  }

  // Full view
  return (
    <div
      className={`
        rounded-lg border overflow-hidden transition-all duration-300
        ${severityStyles.bg} ${severityStyles.border}
        ${isSelected ? 'ring-2 ring-blue-500 shadow-lg' : ''}
        hover:shadow-md hover:-translate-y-0.5 cursor-pointer
      `}
    >
      {/* Header */}
      <div
        className="p-4 cursor-pointer"
        onClick={handleCardClick}
        role="article"
        aria-label={`Conflict: ${conflict.title}`}
      >
        <div className="flex items-start gap-3">
          {/* Severity Icon */}
          <div className={`flex-shrink-0 mt-0.5 ${severityStyles.icon}`} aria-hidden="true">
            <SeverityIcon className="w-6 h-6" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Title and badges row */}
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h3 className={`font-semibold ${severityStyles.text}`}>
                {conflict.title}
              </h3>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${severityStyles.badge}`}>
                {conflict.severity.toUpperCase()}
              </span>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusStyles.bg} ${statusStyles.text}`}>
                <span className={`inline-block w-1.5 h-1.5 rounded-full ${statusStyles.dot} mr-1`} />
                {getStatusLabel(conflict.status)}
              </span>
            </div>

            {/* Type badge */}
            <div className="flex items-center gap-1.5 text-sm text-gray-600 mb-2">
              <TypeIcon className="w-4 h-4" aria-hidden="true" />
              <span>{getTypeLabel(conflict.type)}</span>
            </div>

            {/* Description */}
            <p className={`text-sm ${severityStyles.text} opacity-90`}>
              {conflict.description}
            </p>

            {/* Meta info */}
            <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" aria-hidden="true" />
                {format(new Date(conflict.conflictDate), 'MMM d, yyyy')}
                {conflict.conflictSession && ` (${conflict.conflictSession})`}
              </span>
              <span className="flex items-center gap-1">
                <User className="w-3.5 h-3.5" aria-hidden="true" />
                {conflict.affectedPersonIds.length} affected
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" aria-hidden="true" />
                Detected {format(new Date(conflict.detectedAt), 'MMM d, h:mm a')}
              </span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex-shrink-0 flex items-center gap-2">
            <button
              onClick={handleToggleExpand}
              className="p-1.5 rounded-md hover:bg-white/50 transition-colors"
              aria-label={isExpanded ? 'Collapse conflict details' : 'Expand conflict details'}
              aria-expanded={isExpanded}
            >
              {isExpanded ? (
                <ChevronUp className="w-5 h-5 text-gray-500" aria-hidden="true" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-500" aria-hidden="true" />
              )}
            </button>

            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowActions(!showActions);
                }}
                className="p-1.5 rounded-md hover:bg-white/50 transition-colors"
                aria-label="More actions for this conflict"
                aria-expanded={showActions}
                aria-haspopup="menu"
              >
                <MoreHorizontal className="w-5 h-5 text-gray-500" aria-hidden="true" />
              </button>

              {showActions && (
                <div
                  className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg shadow-lg border z-10"
                  role="menu"
                  aria-label="Conflict actions menu"
                  onMouseLeave={() => setShowActions(false)}
                >
                  {conflict.status === 'unresolved' && onViewSuggestions && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewSuggestions(conflict);
                        setShowActions(false);
                      }}
                      role="menuitem"
                      aria-label="View resolution suggestions for this conflict"
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Lightbulb className="w-4 h-4 text-amber-500" aria-hidden="true" />
                      View Suggestions
                    </button>
                  )}
                  {conflict.status === 'unresolved' && onResolve && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onResolve(conflict);
                        setShowActions(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Check className="w-4 h-4 text-green-500" />
                      Resolve
                    </button>
                  )}
                  {conflict.status === 'unresolved' && onOverride && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOverride(conflict);
                        setShowActions(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Shield className="w-4 h-4 text-blue-500" />
                      Override
                    </button>
                  )}
                  {onViewHistory && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewHistory(conflict);
                        setShowActions(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                    >
                      <History className="w-4 h-4 text-gray-500" />
                      View History
                    </button>
                  )}
                  {conflict.status === 'unresolved' && onIgnore && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onIgnore(conflict);
                        setShowActions(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 text-red-600"
                    >
                      <X className="w-4 h-4" />
                      Ignore
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0 animate-slideDown">
          <div className="border-t border-gray-200/50 pt-4 mt-2">
            {/* Affected assignments */}
            {conflict.affectedAssignmentIds.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Affected Assignments ({conflict.affectedAssignmentIds.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {conflict.affectedAssignmentIds.map((id) => (
                    <span
                      key={id}
                      className="px-2 py-1 bg-white/50 rounded text-xs text-gray-600 font-mono"
                    >
                      {id.slice(0, 8)}...
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Conflict details */}
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Details</h4>
              <pre className="bg-white/50 rounded p-3 text-xs text-gray-600 overflow-x-auto">
                {JSON.stringify(conflict.details, null, 2)}
              </pre>
            </div>

            {/* Resolution info (if resolved) */}
            {conflict.status === 'resolved' && conflict.resolvedAt && (
              <div className="bg-green-100 rounded-lg p-3">
                <h4 className="text-sm font-medium text-green-800 mb-1">Resolution</h4>
                <p className="text-sm text-green-700">
                  Resolved on {format(new Date(conflict.resolvedAt), 'MMM d, yyyy h:mm a')}
                  {conflict.resolvedBy && ` by ${conflict.resolvedBy}`}
                </p>
                {conflict.resolutionMethod && (
                  <p className="text-xs text-green-600 mt-1">
                    Method: {conflict.resolutionMethod.replace('_', ' ')}
                  </p>
                )}
                {conflict.resolutionNotes && (
                  <p className="text-sm text-green-700 mt-2 italic">
                    &ldquo;{conflict.resolutionNotes}&rdquo;
                  </p>
                )}
              </div>
            )}

            {/* Quick actions for unresolved */}
            {conflict.status === 'unresolved' && (
              <div className="flex gap-2 mt-4" role="group" aria-label="Conflict resolution actions">
                {onViewSuggestions && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onViewSuggestions(conflict);
                    }}
                    aria-label="View resolution suggestions"
                    className="flex-1 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-all duration-200 hover:shadow-lg active:scale-95 text-sm font-medium flex items-center justify-center gap-2"
                  >
                    <Lightbulb className="w-4 h-4" aria-hidden="true" />
                    View Suggestions
                  </button>
                )}
                {onResolve && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onResolve(conflict);
                    }}
                    aria-label="Resolve this conflict"
                    className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-all duration-200 hover:shadow-lg active:scale-95 text-sm font-medium flex items-center justify-center gap-2"
                  >
                    <Check className="w-4 h-4" aria-hidden="true" />
                    Resolve
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Exports
// ============================================================================

export { getSeverityStyles, getSeverityIcon, getTypeLabel, getStatusLabel };
