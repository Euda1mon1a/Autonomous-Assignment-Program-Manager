/**
 * Timeline Row Component
 *
 * Renders a single faculty row in the timeline with assignment blocks,
 * workload indicators, and hover interactions.
 */

import React from 'react';
import { User, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import type {
  FacultyTimelineRow,
  TimelineAssignment,
  TimePeriod,
  AssignmentTooltipData,
} from './types';
import {
  WORKLOAD_STATUS_COLORS,
  WORKLOAD_STATUS_LABELS,
  ACTIVITY_TYPE_COLORS,
} from './types';

export interface TimelineRowProps {
  row: FacultyTimelineRow;
  periods: TimePeriod[];
  onAssignmentHover?: (data: AssignmentTooltipData | null) => void;
  onAssignmentClick?: (assignment: TimelineAssignment) => void;
}

export function TimelineRow({
  row,
  periods,
  onAssignmentHover,
  onAssignmentClick,
}: TimelineRowProps) {
  /**
   * Calculate position and width of assignment block
   */
  const getBlockStyle = (assignment: TimelineAssignment) => {
    const timelineStart = new Date(periods[0].startDate);
    const timelineEnd = new Date(periods[periods.length - 1].endDate);
    const assignmentStart = new Date(assignment.startDate);
    const assignmentEnd = new Date(assignment.endDate);

    // Clamp dates to timeline bounds
    const clampedStart = assignmentStart < timelineStart ? timelineStart : assignmentStart;
    const clampedEnd = assignmentEnd > timelineEnd ? timelineEnd : assignmentEnd;

    // Calculate total timeline duration
    const totalDuration = timelineEnd.getTime() - timelineStart.getTime();

    // Calculate block position and width as percentages
    const left = ((clampedStart.getTime() - timelineStart.getTime()) / totalDuration) * 100;
    const width = ((clampedEnd.getTime() - clampedStart.getTime()) / totalDuration) * 100;

    return {
      left: `${left}%`,
      width: `${width}%`,
    };
  };

  /**
   * Get color for assignment block
   */
  const getBlockColor = (assignment: TimelineAssignment) => {
    return ACTIVITY_TYPE_COLORS[assignment.activityType] || ACTIVITY_TYPE_COLORS.default;
  };

  /**
   * Get workload status icon
   */
  const getWorkloadIcon = () => {
    switch (row.workloadStatus) {
      case 'on-track':
        return <CheckCircle className="w-4 h-4" />;
      case 'overloaded':
        return <AlertCircle className="w-4 h-4" />;
      case 'underutilized':
        return <Clock className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="flex border-b border-gray-200 hover:bg-gray-50 transition-colors">
      {/* Faculty info column */}
      <div className="w-64 flex-shrink-0 p-3 border-r border-gray-200 bg-white sticky left-0 z-10">
        <div className="flex items-start gap-2">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
            <User className="w-4 h-4 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium text-gray-900 truncate">{row.facultyName}</h4>
            <p className="text-xs text-gray-500 truncate">{row.specialty}</p>

            {/* Workload status */}
            <div className="flex items-center gap-1.5 mt-1">
              <div
                className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                style={{
                  backgroundColor: `${WORKLOAD_STATUS_COLORS[row.workloadStatus]}20`,
                  color: WORKLOAD_STATUS_COLORS[row.workloadStatus],
                }}
              >
                {getWorkloadIcon()}
                <span>{WORKLOAD_STATUS_LABELS[row.workloadStatus]}</span>
              </div>
            </div>

            {/* Utilization percentage */}
            <div className="mt-1.5">
              <div className="flex items-center justify-between text-xs text-gray-600 mb-0.5">
                <span>Utilization</span>
                <span className="font-medium">{row.utilizationPercentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full transition-all"
                  style={{
                    width: `${Math.min(row.utilizationPercentage, 100)}%`,
                    backgroundColor: WORKLOAD_STATUS_COLORS[row.workloadStatus],
                  }}
                />
              </div>
            </div>

            {/* Total hours */}
            <p className="text-xs text-gray-500 mt-1">
              {row.totalHours} hrs total
            </p>
          </div>
        </div>
      </div>

      {/* Timeline grid */}
      <div className="flex-1 relative min-h-[120px] bg-white">
        {/* Background grid lines */}
        <div className="absolute inset-0 flex">
          {periods.map((period, index) => (
            <div
              key={index}
              className={`flex-1 border-r border-gray-100 ${
                period.isCurrent ? 'bg-blue-50/30' : ''
              }`}
            />
          ))}
        </div>

        {/* Assignment blocks */}
        <div className="absolute inset-0 p-2">
          <div className="relative h-full">
            {row.assignments.map((assignment) => {
              const style = getBlockStyle(assignment);
              const color = getBlockColor(assignment);

              return (
                <div
                  key={assignment.id}
                  className="absolute h-[calc(100%-8px)] top-1 rounded cursor-pointer shadow-sm hover:shadow-md transition-all group"
                  style={{
                    ...style,
                    backgroundColor: color,
                    minWidth: '20px',
                  }}
                  onMouseEnter={(e) => {
                    if (onAssignmentHover) {
                      const rect = e.currentTarget.getBoundingClientRect();
                      onAssignmentHover({
                        assignment,
                        position: { x: rect.left + rect.width / 2, y: rect.top },
                      });
                    }
                  }}
                  onMouseLeave={() => {
                    if (onAssignmentHover) {
                      onAssignmentHover(null);
                    }
                  }}
                  onClick={() => {
                    if (onAssignmentClick) {
                      onAssignmentClick(assignment);
                    }
                  }}
                >
                  {/* Assignment label (only show if wide enough) */}
                  <div className="px-2 py-1 h-full flex items-center justify-center overflow-hidden">
                    <span className="text-xs font-medium text-white truncate group-hover:scale-105 transition-transform">
                      {assignment.rotationName}
                    </span>
                  </div>

                  {/* Status indicator dot */}
                  <div
                    className="absolute top-1 right-1 w-2 h-2 rounded-full border border-white"
                    style={{
                      backgroundColor:
                        assignment.status === 'completed'
                          ? '#22c55e'
                          : assignment.status === 'in-progress'
                          ? '#fbbf24'
                          : '#ffffff',
                    }}
                  />
                </div>
              );
            })}

            {/* Empty state */}
            {row.assignments.length === 0 && (
              <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                No assignments
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Assignment Tooltip Component
 */
export interface AssignmentTooltipProps {
  data: AssignmentTooltipData;
}

export function AssignmentTooltip({ data }: AssignmentTooltipProps) {
  const { assignment, position } = data;

  return (
    <div
      className="fixed z-50 pointer-events-none"
      style={{
        left: `${position.x}px`,
        top: `${position.y - 10}px`,
        transform: 'translate(-50%, -100%)',
      }}
    >
      <div className="bg-gray-900 text-white rounded-lg shadow-xl p-3 max-w-xs">
        {/* Arrow */}
        <div
          className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full"
          style={{
            width: 0,
            height: 0,
            borderLeft: '6px solid transparent',
            borderRight: '6px solid transparent',
            borderTop: '6px solid #111827',
          }}
        />

        {/* Content */}
        <div className="space-y-1.5">
          <h5 className="font-semibold text-sm">{assignment.rotationName}</h5>
          <p className="text-xs text-gray-300">{assignment.facultyName}</p>

          <div className="flex items-center gap-4 text-xs pt-1.5 border-t border-gray-700">
            <div>
              <span className="text-gray-400">Start:</span>{' '}
              <span className="text-white">
                {new Date(assignment.startDate).toLocaleDateString()}
              </span>
            </div>
            <div>
              <span className="text-gray-400">End:</span>{' '}
              <span className="text-white">
                {new Date(assignment.endDate).toLocaleDateString()}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div>
              <span className="text-gray-400">Hours/week:</span>{' '}
              <span className="text-white">{assignment.hoursPerWeek}</span>
            </div>
            <div>
              <span className="text-gray-400">Status:</span>{' '}
              <span className="text-white capitalize">{assignment.status}</span>
            </div>
          </div>

          {assignment.notes && (
            <p className="text-xs text-gray-300 pt-1.5 border-t border-gray-700">
              {assignment.notes}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
