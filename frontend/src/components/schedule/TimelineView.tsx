/**
 * TimelineView Component
 *
 * Gantt-style timeline visualization for schedule assignments
 */

import React, { useState, useMemo } from 'react';
import { RotationBadge } from './RotationBadge';

export interface TimelineAssignment {
  id: string;
  personId: string;
  personName: string;
  rotationType: string;
  startDate: string;
  endDate: string;
  shift?: 'AM' | 'PM' | 'Night';
}

export interface TimelineViewProps {
  assignments: TimelineAssignment[];
  startDate: string;
  endDate: string;
  groupBy?: 'person' | 'rotation';
  onAssignmentClick?: (assignment: TimelineAssignment) => void;
  className?: string;
}

export const TimelineView: React.FC<TimelineViewProps> = ({
  assignments,
  startDate,
  endDate,
  groupBy = 'person',
  onAssignmentClick,
  className = '',
}) => {
  const [hoveredAssignment, setHoveredAssignment] = useState<string | null>(null);

  const start = useMemo(() => new Date(startDate), [startDate]);
  const end = useMemo(() => new Date(endDate), [endDate]);
  const totalDays = useMemo(() => {
    return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
  }, [start, end]);

  // Group assignments
  const groupedAssignments = useMemo(() => {
    const groups: Record<string, TimelineAssignment[]> = {};

    assignments.forEach((assignment) => {
      const key = groupBy === 'person' ? assignment.personId : assignment.rotationType;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(assignment);
    });

    return groups;
  }, [assignments, groupBy]);

  const calculatePosition = (assignmentStart: string, assignmentEnd: string) => {
    const assStart = new Date(assignmentStart);
    const assEnd = new Date(assignmentEnd);

    const left = Math.max(0, (assStart.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) / totalDays * 100;
    const duration = (assEnd.getTime() - assStart.getTime()) / (1000 * 60 * 60 * 24);
    const width = (duration / totalDays) * 100;

    return { left: `${left}%`, width: `${width}%` };
  };

  const getWeekMarkers = () => {
    const markers = [];
    const current = new Date(start);

    while (current <= end) {
      const position = ((current.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) / totalDays * 100;
      markers.push({
        date: new Date(current),
        position,
      });
      current.setDate(current.getDate() + 7);
    }

    return markers;
  };

  return (
    <div className={`timeline-view bg-white rounded-lg shadow p-4 ${className}`}>
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          Timeline View ({groupBy === 'person' ? 'By Person' : 'By Rotation'})
        </h3>
        <div className="text-sm text-gray-600">
          {start.toLocaleDateString()} - {end.toLocaleDateString()}
        </div>
      </div>

      {/* Timeline Grid */}
      <div className="timeline-grid">
        {/* Week markers */}
        <div className="relative h-8 border-b border-gray-300 mb-4">
          {getWeekMarkers().map((marker, idx) => (
            <div
              key={idx}
              className="absolute top-0 h-full border-l border-gray-200"
              style={{ left: `${marker.position}%` }}
            >
              <span className="absolute -top-1 -left-8 text-xs text-gray-500">
                {marker.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
            </div>
          ))}
        </div>

        {/* Assignment rows */}
        {Object.entries(groupedAssignments).map(([groupKey, groupAssignments]) => {
          const groupLabel = groupBy === 'person'
            ? groupAssignments[0]?.personName
            : groupAssignments[0]?.rotationType;

          return (
            <div key={groupKey} className="timeline-row mb-3">
              {/* Row label */}
              <div className="flex items-center mb-2">
                <div className="w-32 font-medium text-sm truncate" title={groupLabel}>
                  {groupLabel}
                </div>
              </div>

              {/* Assignment bars */}
              <div className="relative h-12 bg-gray-50 rounded">
                {groupAssignments.map((assignment) => {
                  const position = calculatePosition(assignment.startDate, assignment.endDate);
                  const isHovered = hoveredAssignment === assignment.id;

                  return (
                    <button
                      key={assignment.id}
                      className={`
                        absolute top-1 h-10 rounded px-2 py-1 transition-all
                        ${isHovered ? 'scale-105 z-10 shadow-lg' : 'shadow'}
                        focus:outline-none focus:ring-2 focus:ring-blue-500
                      `}
                      style={position}
                      onClick={() => onAssignmentClick?.(assignment)}
                      onMouseEnter={() => setHoveredAssignment(assignment.id)}
                      onMouseLeave={() => setHoveredAssignment(null)}
                      aria-label={`${assignment.personName} - ${assignment.rotationType} from ${assignment.startDate} to ${assignment.endDate}`}
                    >
                      <div className="flex items-center justify-center h-full">
                        <RotationBadge
                          rotationType={assignment.rotationType}
                          size="sm"
                          showIcon={parseFloat(position.width) > 10}
                        />
                      </div>

                      {/* Tooltip */}
                      {isHovered && (
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap z-20">
                          {assignment.personName} - {assignment.rotationType}
                          <br />
                          {new Date(assignment.startDate).toLocaleDateString()} -{' '}
                          {new Date(assignment.endDate).toLocaleDateString()}
                          {assignment.shift && ` (${assignment.shift})`}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-600">
          Hover over assignments for details. Click to view full information.
        </div>
      </div>
    </div>
  );
};

export default TimelineView;
