'use client';

/**
 * AuditTimeline Component
 *
 * Visual timeline display of audit log events with
 * grouping by date, interactive tooltips, and filtering.
 */

import { useMemo, useState, useCallback } from 'react';
import { format, parseISO, isSameDay, startOfDay } from 'date-fns';
import {
  Plus,
  Pencil,
  Trash2,
  AlertTriangle,
  RotateCcw,
  Upload,
  Download,
  Calendar,
  CheckCircle,
  LogIn,
  LogOut,
  FileText,
  User,
  ChevronDown,
  ChevronUp,
  Clock,
  Info,
  AlertCircle,
} from 'lucide-react';
import type {
  AuditLogEntry,
  AuditActionType,
  AuditSeverity,
  TimelineEvent,
} from './types';
import {
  ENTITY_TYPE_LABELS,
  ACTION_TYPE_LABELS,
} from './types';

// ============================================================================
// Types
// ============================================================================

interface AuditTimelineProps {
  events: AuditLogEntry[];
  onEventClick?: (event: AuditLogEntry) => void;
  selectedEventId?: string;
  isLoading?: boolean;
  maxHeight?: string;
}

interface TimelineGroup {
  date: Date;
  dateStr: string;
  events: AuditLogEntry[];
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Group events by date
 */
function groupEventsByDate(events: AuditLogEntry[]): TimelineGroup[] {
  const groups = new Map<string, AuditLogEntry[]>();

  events.forEach((event) => {
    const dateKey = format(parseISO(event.timestamp), 'yyyy-MM-dd');
    const existing = groups.get(dateKey) || [];
    groups.set(dateKey, [...existing, event]);
  });

  return Array.from(groups.entries())
    .map(([dateStr, events]) => ({
      date: parseISO(dateStr),
      dateStr,
      events: events.sort(
        (a, b) => parseISO(b.timestamp).getTime() - parseISO(a.timestamp).getTime()
      ),
    }))
    .sort((a, b) => b.date.getTime() - a.date.getTime());
}

/**
 * Get icon component for action type
 */
function getActionIcon(action: AuditActionType): React.ReactNode {
  const iconProps = { className: 'w-4 h-4', 'aria-hidden': 'true' as const };

  switch (action) {
    case 'create':
      return <Plus {...iconProps} />;
    case 'update':
      return <Pencil {...iconProps} />;
    case 'delete':
      return <Trash2 {...iconProps} />;
    case 'override':
      return <AlertTriangle {...iconProps} />;
    case 'restore':
      return <RotateCcw {...iconProps} />;
    case 'bulkImport':
      return <Upload {...iconProps} />;
    case 'bulkDelete':
      return <Trash2 {...iconProps} />;
    case 'scheduleGenerate':
      return <Calendar {...iconProps} />;
    case 'scheduleValidate':
      return <CheckCircle {...iconProps} />;
    case 'login':
      return <LogIn {...iconProps} />;
    case 'logout':
      return <LogOut {...iconProps} />;
    case 'export':
      return <Download {...iconProps} />;
    default:
      return <FileText {...iconProps} />;
  }
}

/**
 * Get color classes for action type
 */
function getActionColors(action: AuditActionType): { bg: string; text: string; border: string } {
  switch (action) {
    case 'create':
      return { bg: 'bg-green-500', text: 'text-green-700', border: 'border-green-500' };
    case 'update':
      return { bg: 'bg-blue-500', text: 'text-blue-700', border: 'border-blue-500' };
    case 'delete':
    case 'bulkDelete':
      return { bg: 'bg-red-500', text: 'text-red-700', border: 'border-red-500' };
    case 'override':
      return { bg: 'bg-orange-500', text: 'text-orange-700', border: 'border-orange-500' };
    case 'restore':
      return { bg: 'bg-purple-500', text: 'text-purple-700', border: 'border-purple-500' };
    case 'bulkImport':
      return { bg: 'bg-indigo-500', text: 'text-indigo-700', border: 'border-indigo-500' };
    case 'scheduleGenerate':
    case 'scheduleValidate':
      return { bg: 'bg-teal-500', text: 'text-teal-700', border: 'border-teal-500' };
    case 'login':
    case 'logout':
      return { bg: 'bg-gray-500', text: 'text-gray-700', border: 'border-gray-500' };
    case 'export':
      return { bg: 'bg-violet-500', text: 'text-violet-700', border: 'border-violet-500' };
    default:
      return { bg: 'bg-gray-400', text: 'text-gray-600', border: 'border-gray-400' };
  }
}

/**
 * Get severity icon and color
 */
function getSeverityConfig(severity: AuditSeverity): {
  icon: React.ReactNode;
  color: string;
} {
  switch (severity) {
    case 'critical':
      return {
        icon: <AlertCircle className="w-3 h-3" aria-hidden="true" />,
        color: 'text-red-600',
      };
    case 'warning':
      return {
        icon: <AlertTriangle className="w-3 h-3" aria-hidden="true" />,
        color: 'text-yellow-600',
      };
    default:
      return {
        icon: <Info className="w-3 h-3" aria-hidden="true" />,
        color: 'text-blue-600',
      };
  }
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Single timeline event card
 */
function TimelineEventCard({
  event,
  isSelected,
  onClick,
}: {
  event: AuditLogEntry;
  isSelected: boolean;
  onClick?: () => void;
}) {
  const colors = getActionColors(event.action);
  const severityConfig = getSeverityConfig(event.severity);
  const timeStr = format(parseISO(event.timestamp), 'HH:mm:ss');

  return (
    <div
      className={`
        relative pl-8 pb-6 cursor-pointer
        before:absolute before:left-3 before:top-0 before:h-full before:w-0.5
        before:bg-gray-200 last:before:hidden
      `}
      onClick={onClick}
      role="listitem"
    >
      {/* Timeline dot */}
      <div
        className={`
          absolute left-0 top-0 w-7 h-7 rounded-full flex items-center justify-center
          ${colors.bg} text-white shadow-md
          ${event.acgmeOverride ? 'ring-2 ring-orange-400 ring-offset-2' : ''}
        `}
      >
        {getActionIcon(event.action)}
      </div>

      {/* Event card */}
      <div
        className={`
          ml-4 p-4 bg-white rounded-lg border shadow-sm transition-all
          ${isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200 hover:shadow-md'}
          ${event.acgmeOverride ? 'bg-orange-50' : ''}
        `}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div>
            <div className="flex items-center gap-2">
              <span className={`font-semibold ${colors.text}`}>
                {ACTION_TYPE_LABELS[event.action]}
              </span>
              {event.acgmeOverride && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-orange-100 text-orange-800 text-xs rounded-full">
                  <AlertTriangle className="w-3 h-3" aria-hidden="true" />
                  ACGME Override
                </span>
              )}
            </div>
            <div className="text-sm text-gray-600">
              {ENTITY_TYPE_LABELS[event.entityType]}
              {event.entityName && (
                <span className="font-medium ml-1">· {event.entityName}</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Clock className="w-3 h-3" aria-hidden="true" />
            {timeStr}
          </div>
        </div>

        {/* User info */}
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
          <User className="w-4 h-4 text-gray-400" aria-hidden="true" />
          <span>{event.user.name}</span>
          {event.severity !== 'info' && (
            <span className={`flex items-center gap-1 ${severityConfig.color}`}>
              {severityConfig.icon}
              {event.severity}
            </span>
          )}
        </div>

        {/* Reason/description */}
        {event.reason && (
          <p className="text-sm text-gray-600 mt-2 pt-2 border-t border-gray-100">
            {event.reason}
          </p>
        )}

        {/* ACGME justification */}
        {event.acgmeOverride && event.acgmeJustification && (
          <div className="mt-2 p-2 bg-orange-100 rounded text-sm text-orange-800">
            <span className="font-medium">Justification: </span>
            {event.acgmeJustification}
          </div>
        )}

        {/* Changes count indicator */}
        {event.changes && event.changes.length > 0 && (
          <div className="mt-2 text-xs text-gray-500">
            {event.changes.length} field{event.changes.length !== 1 ? 's' : ''} changed
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Date group header
 */
function DateGroupHeader({
  date,
  eventCount,
  isExpanded,
  onToggle,
}: {
  date: Date;
  eventCount: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const isToday = isSameDay(date, new Date());
  const dateStr = isToday ? 'Today' : format(date, 'EEEE, MMMM d, yyyy');

  return (
    <button
      type="button"
      onClick={onToggle}
      className="flex items-center gap-3 w-full py-3 px-4 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors mb-4"
      aria-label={`${dateStr}, ${eventCount} event${eventCount !== 1 ? 's' : ''}`}
      aria-expanded={isExpanded}
    >
      <Calendar className="w-5 h-5 text-gray-500" aria-hidden="true" />
      <span className={`font-semibold ${isToday ? 'text-blue-600' : 'text-gray-700'}`}>
        {dateStr}
      </span>
      <span className="text-sm text-gray-500">
        ({eventCount} event{eventCount !== 1 ? 's' : ''})
      </span>
      <div className="ml-auto">
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-400" aria-hidden="true" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" aria-hidden="true" />
        )}
      </div>
    </button>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function AuditTimeline({
  events,
  onEventClick,
  selectedEventId,
  isLoading = false,
  maxHeight = '600px',
}: AuditTimelineProps) {
  const [collapsedDates, setCollapsedDates] = useState<Set<string>>(new Set());

  const groupedEvents = useMemo(() => groupEventsByDate(events), [events]);

  const toggleDateGroup = useCallback((dateStr: string) => {
    setCollapsedDates((prev) => {
      const next = new Set(prev);
      if (next.has(dateStr)) {
        next.delete(dateStr);
      } else {
        next.add(dateStr);
      }
      return next;
    });
  }, []);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6" role="status" aria-live="polite" aria-label="Loading timeline events">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex gap-4">
              <div className="w-7 h-7 bg-gray-200 rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <Clock className="w-12 h-12 text-gray-400 mx-auto mb-3" aria-hidden="true" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">No events found</h3>
        <p className="text-gray-600">
          There are no audit events matching your current filters.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Timeline header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">Activity Timeline</h3>
          <span className="text-sm text-gray-500">
            {events.length} event{events.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Timeline content */}
      <div
        className="p-4 overflow-y-auto"
        style={{ maxHeight }}
        role="list"
        aria-label="Timeline events grouped by date"
      >
        {groupedEvents.map((group) => {
          const isCollapsed = collapsedDates.has(group.dateStr);

          return (
            <div key={group.dateStr} className="mb-6 last:mb-0" role="listitem">
              <DateGroupHeader
                date={group.date}
                eventCount={group.events.length}
                isExpanded={!isCollapsed}
                onToggle={() => toggleDateGroup(group.dateStr)}
              />

              {!isCollapsed && (
                <div className="relative" role="list" aria-label={`Events for ${format(group.date, 'MMMM d, yyyy')}`}>
                  {group.events.map((event) => (
                    <TimelineEventCard
                      key={event.id}
                      event={event}
                      isSelected={selectedEventId === event.id}
                      onClick={() => onEventClick?.(event)}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-500 mb-2">Legend</div>
        <div className="flex flex-wrap gap-4">
          {[
            { action: 'create' as AuditActionType, label: 'Created' },
            { action: 'update' as AuditActionType, label: 'Updated' },
            { action: 'delete' as AuditActionType, label: 'Deleted' },
            { action: 'override' as AuditActionType, label: 'Override' },
          ].map(({ action, label }) => {
            const colors = getActionColors(action);
            return (
              <div key={action} className="flex items-center gap-1.5">
                <div className={`w-3 h-3 rounded-full ${colors.bg}`} />
                <span className="text-xs text-gray-600">{label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
