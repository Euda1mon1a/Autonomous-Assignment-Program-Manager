/**
 * SwapTimeline Component
 *
 * Historical timeline of swap requests and executions
 */

import React from 'react';
import { Badge } from '../ui/Badge';

export interface SwapTimelineEvent {
  id: string;
  swapId: string;
  type: 'created' | 'approved' | 'rejected' | 'cancelled' | 'executed' | 'rolledback';
  timestamp: string;
  actor: {
    id: string;
    name: string;
    role: string;
  };
  details: string;
  notes?: string;
}

export interface SwapTimelineProps {
  events: SwapTimelineEvent[];
  swapId?: string; // Filter to specific swap
  onEventClick?: (event: SwapTimelineEvent) => void;
  className?: string;
}

const eventConfig = {
  created: {
    icon: '📝',
    color: 'bg-blue-100 border-blue-500',
    label: 'Created',
    badgeVariant: 'default' as const,
  },
  approved: {
    icon: '👍',
    color: 'bg-green-100 border-green-500',
    label: 'Approved',
    badgeVariant: 'default' as const,
  },
  rejected: {
    icon: '❌',
    color: 'bg-red-100 border-red-500',
    label: 'Rejected',
    badgeVariant: 'destructive' as const,
  },
  cancelled: {
    icon: '🚫',
    color: 'bg-gray-100 border-gray-500',
    label: 'Cancelled',
    badgeVariant: 'default' as const,
  },
  executed: {
    icon: '✅',
    color: 'bg-green-100 border-green-500',
    label: 'Executed',
    badgeVariant: 'default' as const,
  },
  rolledback: {
    icon: '↩️',
    color: 'bg-orange-100 border-orange-500',
    label: 'Rolled Back',
    badgeVariant: 'warning' as const,
  },
};

export const SwapTimeline: React.FC<SwapTimelineProps> = ({
  events,
  swapId,
  onEventClick,
  className = '',
}) => {
  const filteredEvents = swapId
    ? events.filter(e => e.swapId === swapId)
    : events;

  const sortedEvents = [...filteredEvents].sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  if (sortedEvents.length === 0) {
    return (
      <div className={`swap-timeline bg-white rounded-lg shadow p-6 text-center ${className}`}>
        <div className="text-4xl mb-3">📋</div>
        <p className="text-gray-600">No swap history available</p>
      </div>
    );
  }

  return (
    <div className={`swap-timeline bg-white rounded-lg shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold">Swap History</h3>
        <p className="text-sm text-gray-600 mt-1">
          {sortedEvents.length} event{sortedEvents.length !== 1 ? 's' : ''} recorded
        </p>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical Line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-300" aria-hidden="true" />

        {/* Events */}
        <div className="space-y-4">
          {sortedEvents.map((event, idx) => {
            const config = eventConfig[event.type];

            return (
              <div key={event.id} className="relative pl-16">
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
                  disabled={!onEventClick}
                  className={`
                    w-full text-left border-l-4 rounded-lg p-4 transition-all bg-white shadow-sm
                    ${config.color}
                    ${onEventClick ? 'hover:shadow-md cursor-pointer' : ''}
                    focus:outline-none focus:ring-2 focus:ring-blue-500
                  `}
                >
                  {/* Timestamp */}
                  <div className="text-xs text-gray-600 mb-2">
                    {new Date(event.timestamp).toLocaleString('en-US', {
                      weekday: 'short',
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>

                  {/* Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xl" role="img" aria-label={config.label}>
                        {config.icon}
                      </span>
                      <h4 className="font-semibold">{config.label}</h4>
                    </div>
                    <Badge variant={config.badgeVariant}>{event.type}</Badge>
                  </div>

                  {/* Actor */}
                  <div className="text-sm mb-2">
                    <span className="font-medium">{event.actor.name}</span>
                    <span className="text-gray-600"> ({event.actor.role})</span>
                  </div>

                  {/* Details */}
                  <p className="text-sm text-gray-700 mb-2">{event.details}</p>

                  {/* Notes (if any) */}
                  {event.notes && (
                    <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-200 text-sm">
                      <span className="font-medium">Notes: </span>
                      {event.notes}
                    </div>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SwapTimeline;
