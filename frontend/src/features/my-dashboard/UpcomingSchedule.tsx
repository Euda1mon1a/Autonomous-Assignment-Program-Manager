'use client';

/**
 * UpcomingSchedule Component
 *
 * Displays a list of upcoming assignments with details like date, time,
 * location, and activity. Includes action buttons for requesting swaps
 * when assignments are tradeable.
 */

import { useState } from 'react';
import { format, parseISO, isToday, isTomorrow, isWithinInterval, addDays } from 'date-fns';
import {
  Calendar,
  Clock,
  MapPin,
  AlertCircle,
  ArrowRightLeft,
  Loader2,
  CheckCircle,
} from 'lucide-react';
import type { UpcomingAssignment } from './types';
import { TIME_OF_DAY_LABELS, LOCATION_LABELS, LOCATION_COLORS } from './types';
import { useRequestSwap } from './hooks';

// ============================================================================
// Types
// ============================================================================

interface UpcomingScheduleProps {
  assignments: UpcomingAssignment[];
  isLoading?: boolean;
  onSwapRequested?: () => void;
}

interface AssignmentCardProps {
  assignment: UpcomingAssignment;
  onSwapRequested?: () => void;
}

// ============================================================================
// Assignment Card Component
// ============================================================================

function AssignmentCard({ assignment, onSwapRequested }: AssignmentCardProps) {
  const [showSwapForm, setShowSwapForm] = useState(false);
  const [reason, setReason] = useState('');

  const swapMutation = useRequestSwap();

  const assignmentDate = parseISO(assignment.date);
  const isUpcoming = isWithinInterval(assignmentDate, {
    start: new Date(),
    end: addDays(new Date(), 7),
  });

  const handleRequestSwap = async () => {
    try {
      await swapMutation.mutateAsync({
        assignmentId: assignment.id,
        reason: reason || undefined,
      });
      setShowSwapForm(false);
      setReason('');
      onSwapRequested?.();
    } catch (error) {
      // console.error('Failed to request swap:', error);
    }
  };

  // Determine date label
  let dateLabel = format(assignmentDate, 'MMM d, yyyy');
  if (isToday(assignmentDate)) {
    dateLabel = `Today (${format(assignmentDate, 'MMM d')})`;
  } else if (isTomorrow(assignmentDate)) {
    dateLabel = `Tomorrow (${format(assignmentDate, 'MMM d')})`;
  }

  const locationColor = LOCATION_COLORS[assignment.location] || 'gray';

  return (
    <div
      className={`bg-white rounded-lg border ${
        assignment.isConflict ? 'border-red-300 bg-red-50/30' : 'border-gray-200'
      } p-4 hover:shadow-md transition-all ${isUpcoming ? 'ring-2 ring-blue-500/20' : ''}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3 gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Calendar className="w-4 h-4 text-gray-500 flex-shrink-0" />
            <span className="text-sm font-semibold text-gray-900 truncate">{dateLabel}</span>
            {isUpcoming && (
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                Soon
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-500 flex-shrink-0" />
            <span className="text-sm text-gray-600 truncate">
              {TIME_OF_DAY_LABELS[assignment.timeOfDay]}
            </span>
          </div>
        </div>
        <span
          className={`px-2 py-1 bg-${locationColor}-100 text-${locationColor}-700 text-xs font-medium rounded whitespace-nowrap`}
        >
          {LOCATION_LABELS[assignment.location]}
        </span>
      </div>

      {/* Activity */}
      <div className="mb-3">
        <p className="text-sm text-gray-700 font-medium">{assignment.activity}</p>
      </div>

      {/* Conflict Warning */}
      {assignment.isConflict && assignment.conflictReason && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-red-700">{assignment.conflictReason}</p>
        </div>
      )}

      {/* Mutation Error */}
      {swapMutation.isError && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{swapMutation.error?.message}</span>
        </div>
      )}

      {/* Success Message */}
      {swapMutation.isSuccess && (
        <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700 flex items-start gap-2">
          <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>Swap request created successfully!</span>
        </div>
      )}

      {/* Swap Request Form */}
      {!showSwapForm && assignment.canTrade && !swapMutation.isSuccess && (
        <button
          onClick={() => setShowSwapForm(true)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={swapMutation.isPending}
        >
          <ArrowRightLeft className="w-4 h-4" />
          Request Swap
        </button>
      )}

      {showSwapForm && (
        <div className="space-y-3 pt-3 border-t border-gray-200">
          <textarea
            placeholder="Reason for swap request (optional)..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            rows={3}
            disabled={swapMutation.isPending}
          />
          <div className="flex gap-2">
            <button
              onClick={handleRequestSwap}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={swapMutation.isPending}
            >
              {swapMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                'Submit Request'
              )}
            </button>
            <button
              onClick={() => {
                setShowSwapForm(false);
                setReason('');
              }}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={swapMutation.isPending}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {!assignment.canTrade && (
        <div className="text-xs text-gray-500 text-center py-2">
          This assignment cannot be traded
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function UpcomingSchedule({
  assignments,
  isLoading = false,
  onSwapRequested,
}: UpcomingScheduleProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-24"></div>
              </div>
              <div className="h-6 bg-gray-200 rounded w-16"></div>
            </div>
            <div className="h-4 bg-gray-200 rounded w-full mb-3"></div>
            <div className="h-10 bg-gray-200 rounded w-full"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!assignments || assignments.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-8 text-center">
        <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600 font-medium mb-1">No upcoming assignments</p>
        <p className="text-sm text-gray-500">Your schedule is clear for the selected period</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {assignments.map((assignment) => (
        <AssignmentCard
          key={assignment.id}
          assignment={assignment}
          onSwapRequested={onSwapRequested}
        />
      ))}
    </div>
  );
}
