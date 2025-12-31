/**
 * ComplianceTimeline Component
 *
 * Historical view of ACGME compliance over time
 */

import React from 'react';
import { Badge } from '../ui/Badge';

export interface ComplianceEvent {
  id: string;
  date: string;
  type: 'compliant' | 'warning' | 'violation';
  category: string;
  message: string;
  details?: Record<string, any>;
}

export interface ComplianceTimelineProps {
  events: ComplianceEvent[];
  startDate?: string;
  endDate?: string;
  onEventClick?: (event: ComplianceEvent) => void;
  className?: string;
}

const typeConfig = {
  compliant: {
    icon: '✅',
    color: 'bg-green-100 border-green-500',
    badgeVariant: 'default' as const,
  },
  warning: {
    icon: '⚠️',
    color: 'bg-yellow-100 border-yellow-500',
    badgeVariant: 'warning' as const,
  },
  violation: {
    icon: '🚨',
    color: 'bg-red-100 border-red-500',
    badgeVariant: 'destructive' as const,
  },
};

export const ComplianceTimeline: React.FC<ComplianceTimelineProps> = ({
  events,
  startDate,
  endDate,
  onEventClick,
  className = '',
}) => {
  const sortedEvents = [...events].sort((a, b) =>
    new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  const stats = {
    total: events.length,
    violations: events.filter(e => e.type === 'violation').length,
    warnings: events.filter(e => e.type === 'warning').length,
    compliant: events.filter(e => e.type === 'compliant').length,
  };

  return (
    <div className={`compliance-timeline bg-white rounded-lg shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-2">Compliance History</h3>
        {startDate && endDate && (
          <p className="text-sm text-gray-600">
            {new Date(startDate).toLocaleDateString()} - {new Date(endDate).toLocaleDateString()}
          </p>
        )}

        {/* Summary Stats */}
        <div className="flex gap-4 mt-4">
          <div className="flex items-center gap-2">
            <Badge variant="destructive">{stats.violations} Violations</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="warning">{stats.warnings} Warnings</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Badge>{stats.compliant} Compliant</Badge>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical Line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-300" aria-hidden="true" />

        {/* Events */}
        <div className="space-y-6">
          {sortedEvents.map((event, idx) => {
            const config = typeConfig[event.type];

            return (
              <div
                key={event.id}
                className="relative pl-16"
              >
                {/* Timeline Dot */}
                <div
                  className={`
                    absolute left-3 w-6 h-6 rounded-full border-4 border-white shadow-sm
                    ${config.color}
                  `}
                  aria-hidden="true"
                />

                {/* Event Card */}
                <button
                  onClick={() => onEventClick?.(event)}
                  className={`
                    w-full text-left border-l-4 rounded-lg p-4 transition-all
                    ${config.color}
                    ${onEventClick ? 'hover:shadow-md cursor-pointer' : ''}
                    focus:outline-none focus:ring-2 focus:ring-blue-500
                  `}
                >
                  {/* Date */}
                  <div className="text-xs text-gray-600 mb-1">
                    {new Date(event.date).toLocaleDateString('en-US', {
                      weekday: 'short',
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </div>

                  {/* Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg" role="img" aria-label={event.type}>
                        {config.icon}
                      </span>
                      <h4 className="font-semibold">{event.category}</h4>
                    </div>
                    <Badge variant={config.badgeVariant}>
                      {event.type}
                    </Badge>
                  </div>

                  {/* Message */}
                  <p className="text-sm">{event.message}</p>

                  {/* Details (if any) */}
                  {event.details && Object.keys(event.details).length > 0 && (
                    <div className="mt-2 text-xs bg-white bg-opacity-50 rounded p-2">
                      {Object.entries(event.details).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-gray-600">{key}:</span>
                          <span className="font-medium">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* Empty State */}
        {sortedEvents.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-2">📋</div>
            <p>No compliance events recorded</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComplianceTimeline;
