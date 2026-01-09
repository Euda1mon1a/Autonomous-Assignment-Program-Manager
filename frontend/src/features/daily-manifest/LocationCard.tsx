'use client';

import { useState } from 'react';
import { MapPin, ChevronDown, ChevronUp, User, Clock, Activity } from 'lucide-react';
import { StaffingSummary } from './StaffingSummary';
import type { LocationManifest, PersonAssignment } from './types';

// ============================================================================
// Props
// ============================================================================

interface LocationCardProps {
  location: LocationManifest;
  timeOfDay: 'AM' | 'PM' | 'ALL';
}

// ============================================================================
// Helper Functions
// ============================================================================

function getRoleTypeColor(roleType?: string): string {
  switch (roleType) {
    case 'resident':
      return 'text-blue-700 bg-blue-50 border-blue-200';
    case 'faculty':
      return 'text-purple-700 bg-purple-50 border-purple-200';
    case 'fellow':
      return 'text-green-700 bg-green-50 border-green-200';
    default:
      return 'text-gray-700 bg-gray-50 border-gray-200';
  }
}

function getPGYBadgeColor(pgyLevel?: number): string {
  if (!pgyLevel) return 'bg-gray-100 text-gray-600';

  switch (pgyLevel) {
    case 1:
      return 'bg-green-100 text-green-700';
    case 2:
      return 'bg-blue-100 text-blue-700';
    case 3:
      return 'bg-purple-100 text-purple-700';
    case 4:
    case 5:
      return 'bg-orange-100 text-orange-700';
    default:
      return 'bg-gray-100 text-gray-600';
  }
}

// ============================================================================
// Person Assignment Item Component
// ============================================================================

function PersonAssignmentItem({ assignment }: { assignment: PersonAssignment }) {
  const roleTypeColor = getRoleTypeColor(assignment.person.role_type);
  const pgyBadgeColor = getPGYBadgeColor(assignment.person.pgyLevel);

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${roleTypeColor}`}>
      <div className="flex-shrink-0 mt-0.5">
        <User className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <h4 className="font-medium text-sm">{assignment.person.name}</h4>
          {assignment.person.pgyLevel && (
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${pgyBadgeColor}`}>
              PGY-{assignment.person.pgyLevel}
            </span>
          )}
        </div>

        <div className="space-y-1">
          <p className="text-xs flex items-center gap-1.5">
            <Activity className="w-3 h-3" />
            <span className="font-medium">Role:</span> {assignment.role}
          </p>
          <p className="text-xs flex items-center gap-1.5">
            <Clock className="w-3 h-3" />
            <span className="font-medium">Activity:</span> {assignment.activity}
          </p>
          {assignment.rotation_name && (
            <p className="text-xs opacity-75">
              Rotation: {assignment.rotation_name}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function LocationCard({ location, timeOfDay }: LocationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const assignments = timeOfDay === 'ALL'
    ? [...(location.time_slots.AM || []), ...(location.time_slots.PM || [])]
    : location.time_slots[timeOfDay] || [];

  const hasCapacity = location.capacity !== undefined;
  const isNearCapacity = hasCapacity &&
    location.capacity!.current >= location.capacity!.maximum * 0.9;
  const isOverCapacity = hasCapacity &&
    location.capacity!.current > location.capacity!.maximum;

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="flex-shrink-0 mt-1">
              <MapPin className="w-5 h-5 text-blue-600" />
            </div>

            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {location.clinic_location}
              </h3>

              <StaffingSummary
                total={location.staffing_summary.total}
                residents={location.staffing_summary.residents}
                faculty={location.staffing_summary.faculty}
                fellows={location.staffing_summary.fellows}
                compact
              />

              {hasCapacity && (
                <div className="mt-2">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-gray-600">Capacity:</span>
                    <span className={`font-medium ${
                      isOverCapacity ? 'text-red-600' :
                      isNearCapacity ? 'text-amber-600' :
                      'text-green-600'
                    }`}>
                      {location.capacity!.current} / {location.capacity!.maximum}
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-200 rounded-full mt-1 overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        isOverCapacity ? 'bg-red-500' :
                        isNearCapacity ? 'bg-amber-500' :
                        'bg-green-500'
                      }`}
                      style={{
                        width: `${Math.min((location.capacity!.current / location.capacity!.maximum) * 100, 100)}%`
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex-shrink-0 flex flex-col items-end gap-2">
            <button
              className="p-1 rounded hover:bg-gray-100 transition-colors"
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? (
                <ChevronUp className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              )}
            </button>
            <span className="text-xs text-gray-500 font-medium">
              {assignments.length} staff
            </span>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-100">
          <div className="pt-4">
            <StaffingSummary
              total={location.staffing_summary.total}
              residents={location.staffing_summary.residents}
              faculty={location.staffing_summary.faculty}
              fellows={location.staffing_summary.fellows}
            />

            {timeOfDay === 'ALL' ? (
              <div className="mt-4 space-y-4">
                {location.time_slots.AM && location.time_slots.AM.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Morning (AM)
                    </h4>
                    <div className="space-y-2">
                      {location.time_slots.AM.map((assignment, idx) => (
                        <PersonAssignmentItem key={`am-${idx}`} assignment={assignment} />
                      ))}
                    </div>
                  </div>
                )}

                {location.time_slots.PM && location.time_slots.PM.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Afternoon (PM)
                    </h4>
                    <div className="space-y-2">
                      {location.time_slots.PM.map((assignment, idx) => (
                        <PersonAssignmentItem key={`pm-${idx}`} assignment={assignment} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="mt-4 space-y-2">
                {assignments.length > 0 ? (
                  assignments.map((assignment, idx) => (
                    <PersonAssignmentItem key={idx} assignment={assignment} />
                  ))
                ) : (
                  <div className="text-center py-6 text-gray-500 text-sm">
                    No assignments for this time period
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
