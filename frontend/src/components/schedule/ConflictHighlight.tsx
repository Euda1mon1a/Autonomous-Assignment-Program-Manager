/**
 * ConflictHighlight Component
 *
 * Overlay component to highlight schedule conflicts with detailed information
 */

import React from 'react';
import { Badge } from '../ui/Badge';

export interface Conflict {
  id: string;
  type: 'overlap' | 'acgme_violation' | 'coverage_gap' | 'credential_missing';
  severity: 'critical' | 'warning' | 'info';
  message: string;
  affectedPersons: string[];
  affectedDates: string[];
  suggestions?: string[];
}

export interface ConflictHighlightProps {
  conflicts: Conflict[];
  onResolve?: (conflictId: string) => void;
  onDismiss?: (conflictId: string) => void;
  className?: string;
}

const severityConfig = {
  critical: {
    color: 'bg-red-50 border-red-500 text-red-900',
    badgeVariant: 'destructive' as const,
    icon: '🚨',
    label: 'Critical',
  },
  warning: {
    color: 'bg-yellow-50 border-yellow-500 text-yellow-900',
    badgeVariant: 'warning' as const,
    icon: '⚠️',
    label: 'Warning',
  },
  info: {
    color: 'bg-blue-50 border-blue-500 text-blue-900',
    badgeVariant: 'default' as const,
    icon: 'ℹ️',
    label: 'Info',
  },
};

const typeLabels = {
  overlap: 'Schedule Overlap',
  acgme_violation: 'ACGME Violation',
  coverage_gap: 'Coverage Gap',
  credential_missing: 'Missing Credentials',
};

export const ConflictHighlight: React.FC<ConflictHighlightProps> = ({
  conflicts,
  onResolve,
  onDismiss,
  className = '',
}) => {
  if (conflicts.length === 0) {
    return null;
  }

  // Group conflicts by severity
  const groupedConflicts = {
    critical: conflicts.filter(c => c.severity === 'critical'),
    warning: conflicts.filter(c => c.severity === 'warning'),
    info: conflicts.filter(c => c.severity === 'info'),
  };

  return (
    <div className={`conflict-highlight space-y-3 ${className}`}>
      {/* Summary */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold">Schedule Conflicts</h3>
          <div className="flex gap-2">
            {groupedConflicts.critical.length > 0 && (
              <Badge variant="destructive">
                {groupedConflicts.critical.length} Critical
              </Badge>
            )}
            {groupedConflicts.warning.length > 0 && (
              <Badge variant="warning">
                {groupedConflicts.warning.length} Warnings
              </Badge>
            )}
          </div>
        </div>
        <p className="text-sm text-gray-600">
          {conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''} detected. Review and resolve below.
        </p>
      </div>

      {/* Conflict List */}
      <div className="space-y-2">
        {conflicts.map((conflict) => {
          const config = severityConfig[conflict.severity];

          return (
            <div
              key={conflict.id}
              className={`
                rounded-lg border-l-4 p-4 shadow-sm
                ${config.color}
              `}
              role="alert"
              aria-live="polite"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xl" aria-hidden="true">
                    {config.icon}
                  </span>
                  <div>
                    <h4 className="font-semibold">{typeLabels[conflict.type]}</h4>
                    <Badge variant={config.badgeVariant} className="mt-1">
                      {config.label}
                    </Badge>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  {onResolve && (
                    <button
                      onClick={() => onResolve(conflict.id)}
                      className="text-sm px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      aria-label="Resolve conflict"
                    >
                      Resolve
                    </button>
                  )}
                  {onDismiss && (
                    <button
                      onClick={() => onDismiss(conflict.id)}
                      className="text-sm px-2 py-1 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      aria-label="Dismiss conflict"
                    >
                      <span aria-hidden="true">✕</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Message */}
              <p className="text-sm mb-3">{conflict.message}</p>

              {/* Affected Details */}
              <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                <div>
                  <span className="font-medium">Affected Persons:</span>
                  <div className="mt-1">
                    {conflict.affectedPersons.map((person, idx) => (
                      <span key={idx} className="inline-block bg-white px-2 py-0.5 rounded mr-1 mb-1 text-xs">
                        {person}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="font-medium">Affected Dates:</span>
                  <div className="mt-1">
                    {conflict.affectedDates.map((date, idx) => (
                      <span key={idx} className="inline-block bg-white px-2 py-0.5 rounded mr-1 mb-1 text-xs">
                        {new Date(date).toLocaleDateString()}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Suggestions */}
              {conflict.suggestions && conflict.suggestions.length > 0 && (
                <div className="bg-white bg-opacity-50 rounded p-2">
                  <span className="font-medium text-sm">Suggestions:</span>
                  <ul className="list-disc list-inside text-sm mt-1 space-y-1">
                    {conflict.suggestions.map((suggestion, idx) => (
                      <li key={idx}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ConflictHighlight;
