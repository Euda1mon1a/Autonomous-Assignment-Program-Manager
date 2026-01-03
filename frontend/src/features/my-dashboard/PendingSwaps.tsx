'use client';

/**
 * PendingSwaps Component
 *
 * Displays a list of pending swap requests (both incoming and outgoing).
 * Shows swap details and provides quick action buttons to respond to
 * incoming requests.
 */

import { format, parseISO } from 'date-fns';
import {
  ArrowRightLeft,
  ArrowRight,
  Calendar,
  Clock,
  MessageSquare,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import type { PendingSwapSummary } from './types';

// ============================================================================
// Types
// ============================================================================

interface PendingSwapsProps {
  swaps: PendingSwapSummary[];
  isLoading?: boolean;
  onSwapAction?: (swapId: string) => void;
}

interface SwapCardProps {
  swap: PendingSwapSummary;
  onAction?: (swapId: string) => void;
}

// ============================================================================
// Swap Card Component
// ============================================================================

function SwapCard({ swap, onAction }: SwapCardProps) {
  const weekDate = parseISO(swap.weekDate);
  const requestedDate = parseISO(swap.requestedAt);

  const isIncoming = swap.type === 'incoming';
  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-all">
      {/* Header */}
      <div className="flex items-start justify-between mb-3 gap-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {isIncoming ? (
            <ArrowRight className="w-5 h-5 text-blue-600 flex-shrink-0" />
          ) : (
            <ArrowRightLeft className="w-5 h-5 text-gray-600 flex-shrink-0" />
          )}
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-gray-900 truncate">
              {isIncoming ? 'Incoming Request' : 'Outgoing Request'}
            </h3>
            <p className="text-sm text-gray-500 truncate">
              {isIncoming ? `from ${swap.otherFacultyName}` : `to ${swap.otherFacultyName}`}
            </p>
          </div>
        </div>
        <span className={`px-2 py-1 ${statusColors[swap.status]} text-xs font-medium rounded whitespace-nowrap`}>
          {swap.status.charAt(0).toUpperCase() + swap.status.slice(1)}
        </span>
      </div>

      {/* Details */}
      <div className="space-y-2 mb-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Calendar className="w-4 h-4 flex-shrink-0" />
          <span className="truncate">Week: {format(weekDate, 'MMM d, yyyy')}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Clock className="w-4 h-4 flex-shrink-0" />
          <span className="truncate">Requested {format(requestedDate, 'MMM d, yyyy')}</span>
        </div>
      </div>

      {/* Reason */}
      {swap.reason && (
        <div className="mb-3 p-2 bg-gray-50 rounded text-sm text-gray-700">
          <MessageSquare className="inline w-4 h-4 mr-1 flex-shrink-0" />
          <span className="line-clamp-2">{swap.reason}</span>
        </div>
      )}

      {/* Action Buttons */}
      {swap.canRespond && swap.status === 'pending' && (
        <div className="flex gap-2">
          <button
            onClick={() => onAction?.(swap.id)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm font-medium"
          >
            <CheckCircle className="w-4 h-4" />
            Accept
          </button>
          <button
            onClick={() => onAction?.(swap.id)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
          >
            <XCircle className="w-4 h-4" />
            Reject
          </button>
        </div>
      )}

      {!swap.canRespond && swap.status === 'pending' && (
        <div className="text-xs text-gray-500 text-center py-2">
          Waiting for response...
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function PendingSwaps({ swaps, isLoading = false, onSwapAction }: PendingSwapsProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-24"></div>
              </div>
              <div className="h-6 bg-gray-200 rounded w-16"></div>
            </div>
            <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
            <div className="flex gap-2">
              <div className="flex-1 h-10 bg-gray-200 rounded"></div>
              <div className="flex-1 h-10 bg-gray-200 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!swaps || swaps.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-8 text-center">
        <ArrowRightLeft className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600 font-medium mb-1">No pending swap requests</p>
        <p className="text-sm text-gray-500">You have no incoming or outgoing swap requests</p>
      </div>
    );
  }

  // Separate incoming and outgoing
  const incomingSwaps = swaps.filter((s) => s.type === 'incoming');
  const outgoingSwaps = swaps.filter((s) => s.type === 'outgoing');

  return (
    <div className="space-y-4">
      {incomingSwaps.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Incoming ({incomingSwaps.length})
          </h3>
          <div className="space-y-3">
            {incomingSwaps.map((swap) => (
              <SwapCard key={swap.id} swap={swap} onAction={onSwapAction} />
            ))}
          </div>
        </div>
      )}

      {outgoingSwaps.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Outgoing ({outgoingSwaps.length})
          </h3>
          <div className="space-y-3">
            {outgoingSwaps.map((swap) => (
              <SwapCard key={swap.id} swap={swap} onAction={onSwapAction} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
