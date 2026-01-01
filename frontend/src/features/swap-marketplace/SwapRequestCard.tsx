'use client';

/**
 * SwapRequestCard Component
 *
 * Displays a swap request with details and action buttons.
 * Shows source/target faculty, weeks, status, and available actions.
 */

import { useState } from 'react';
import { format, parseISO } from 'date-fns';
import {
  Calendar,
  User,
  ArrowRight,
  CheckCircle,
  XCircle,
  Trash2,
  Clock,
  MessageSquare,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import type { SwapRequest, MarketplaceEntry } from './types';
import {
  SWAP_STATUS_LABELS,
  SWAP_TYPE_LABELS,
  SWAP_STATUS_COLORS,
  SwapType,
} from './types';
import { useAcceptSwap, useRejectSwap, useCancelSwap } from './hooks';

// ============================================================================
// Types
// ============================================================================

interface SwapRequestCardProps {
  swap?: SwapRequest;
  marketplaceEntry?: MarketplaceEntry;
  onActionComplete?: () => void;
}

// ============================================================================
// Component
// ============================================================================

export function SwapRequestCard({
  swap,
  marketplaceEntry,
  onActionComplete,
}: SwapRequestCardProps) {
  const [showNotes, setShowNotes] = useState(false);
  const [notes, setNotes] = useState('');
  const [actionMode, setActionMode] = useState<'accept' | 'reject' | null>(null);

  // Mutations
  const acceptMutation = useAcceptSwap(swap?.id || '');
  const rejectMutation = useRejectSwap(swap?.id || '');
  const cancelMutation = useCancelSwap(swap?.id || '');

  if (!swap && !marketplaceEntry) {
    return null;
  }

  // Handle marketplace entry display
  if (marketplaceEntry) {
    const weekDate = parseISO(marketplaceEntry.weekAvailable);
    const postedDate = parseISO(marketplaceEntry.postedAt);

    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-lg transition-all hover:border-blue-300">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <User className="w-5 h-5 text-gray-500 flex-shrink-0" aria-hidden="true" />
            <h3 className="font-semibold text-gray-900 truncate">
              {marketplaceEntry.requestingFacultyName}
            </h3>
          </div>
          {marketplaceEntry.isCompatible && (
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded whitespace-nowrap ml-2">
              Compatible
            </span>
          )}
        </div>

        <div className="space-y-2 mb-3">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Calendar className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
            <span className="truncate">Week: {format(weekDate, 'MMM d, yyyy')}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Clock className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
            <span className="truncate">Posted {format(postedDate, 'MMM d, yyyy')}</span>
          </div>
        </div>

        {marketplaceEntry.reason && (
          <div className="mb-3 p-2 bg-gray-50 rounded text-sm text-gray-700 line-clamp-3">
            <MessageSquare className="inline w-4 h-4 mr-1 flex-shrink-0" aria-hidden="true" />
            {marketplaceEntry.reason}
          </div>
        )}

        <button
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          onClick={() => {
            // Handle viewing details or requesting swap
          }}
          aria-label={`View details for swap from ${marketplaceEntry.requestingFacultyName}`}
        >
          View Details
          <ArrowRight className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    );
  }

  // Handle swap request display
  if (!swap) {
    return null;
  }

  const statusColor = SWAP_STATUS_COLORS[swap.status];
  const sourceWeekDate = swap.sourceWeek ? parseISO(swap.sourceWeek) : null;
  const targetWeekDate = swap.targetWeek ? parseISO(swap.targetWeek) : null;
  const isAbsorb = swap.swapType === SwapType.ABSORB;

  const handleAccept = async () => {
    try {
      await acceptMutation.mutateAsync({ notes: notes || undefined });
      setActionMode(null);
      setNotes('');
      onActionComplete?.();
    } catch (error) {
      // console.error('Failed to accept swap:', error);
    }
  };

  const handleReject = async () => {
    try {
      await rejectMutation.mutateAsync({ notes: notes || undefined });
      setActionMode(null);
      setNotes('');
      onActionComplete?.();
    } catch (error) {
      // console.error('Failed to reject swap:', error);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this swap request?')) {
      return;
    }

    try {
      await cancelMutation.mutateAsync();
      onActionComplete?.();
    } catch (error) {
      // console.error('Failed to cancel swap:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-lg transition-all hover:border-blue-300">
      {/* Header */}
      <div className="flex items-start justify-between mb-3 gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-gray-900 truncate">
            {SWAP_TYPE_LABELS[swap.swapType]}
          </h3>
          <p className="text-sm text-gray-500">
            {swap.isIncoming ? 'Incoming Request' : 'Outgoing Request'}
          </p>
        </div>
        <span
          className={`px-2 py-1 bg-${statusColor}-100 text-${statusColor}-700 text-xs font-medium rounded whitespace-nowrap`}
        >
          {SWAP_STATUS_LABELS[swap.status]}
        </span>
      </div>

      {/* Faculty and Week Details */}
      <div className="space-y-3 mb-4">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <User className="w-4 h-4 text-gray-500" aria-hidden="true" />
              <span className="text-sm font-medium">{swap.sourceFacultyName}</span>
            </div>
            {sourceWeekDate && (
              <div className="flex items-center gap-2 text-sm text-gray-600 ml-6">
                <Calendar className="w-3 h-3" aria-hidden="true" />
                {format(sourceWeekDate, 'MMM d, yyyy')}
              </div>
            )}
          </div>

          {!isAbsorb && swap.targetFacultyName && (
            <>
              <ArrowRight className="w-5 h-5 text-gray-400" aria-hidden="true" />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <User className="w-4 h-4 text-gray-500" aria-hidden="true" />
                  <span className="text-sm font-medium">{swap.targetFacultyName}</span>
                </div>
                {targetWeekDate && (
                  <div className="flex items-center gap-2 text-sm text-gray-600 ml-6">
                    <Calendar className="w-3 h-3" aria-hidden="true" />
                    {format(targetWeekDate, 'MMM d, yyyy')}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Reason */}
      {swap.reason && (
        <div className="mb-4 p-2 bg-gray-50 rounded text-sm text-gray-700">
          <MessageSquare className="inline w-4 h-4 mr-1" aria-hidden="true" />
          {swap.reason}
        </div>
      )}

      {/* Mutation Errors */}
      {(acceptMutation.isError || rejectMutation.isError || cancelMutation.isError) && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700 flex items-start gap-2" role="alert">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span>
            {acceptMutation.error?.message ||
             rejectMutation.error?.message ||
             cancelMutation.error?.message}
          </span>
        </div>
      )}

      {/* Action Buttons */}
      {!actionMode && (
        <div className="flex gap-2">
          {swap.canAccept && (
            <button
              onClick={() => setActionMode('accept')}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={acceptMutation.isPending || rejectMutation.isPending || cancelMutation.isPending}
              aria-label="Accept swap request"
            >
              {acceptMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  Processing...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" aria-hidden="true" />
                  Accept
                </>
              )}
            </button>
          )}
          {swap.canReject && (
            <button
              onClick={() => setActionMode('reject')}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={acceptMutation.isPending || rejectMutation.isPending || cancelMutation.isPending}
              aria-label="Reject swap request"
            >
              {rejectMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  Processing...
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4" aria-hidden="true" />
                  Reject
                </>
              )}
            </button>
          )}
          {swap.canCancel && (
            <button
              onClick={handleCancel}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={acceptMutation.isPending || rejectMutation.isPending || cancelMutation.isPending}
              aria-label="Cancel swap request"
            >
              {cancelMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  Cancelling...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4" aria-hidden="true" />
                  Cancel
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Accept/Reject with Notes */}
      {actionMode && (
        <div className="space-y-3 pt-3 border-t border-gray-200">
          <textarea
            placeholder={`Add optional notes for ${actionMode === 'accept' ? 'accepting' : 'rejecting'}...`}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            disabled={acceptMutation.isPending || rejectMutation.isPending}
            aria-label={`Optional notes for ${actionMode === 'accept' ? 'accepting' : 'rejecting'} swap request`}
          />
          <div className="flex gap-2">
            <button
              onClick={actionMode === 'accept' ? handleAccept : handleReject}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                actionMode === 'accept'
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-red-600 hover:bg-red-700'
              }`}
              disabled={acceptMutation.isPending || rejectMutation.isPending}
              aria-label={`Confirm ${actionMode === 'accept' ? 'accept' : 'reject'} swap request`}
            >
              {(acceptMutation.isPending || rejectMutation.isPending) && (
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
              )}
              {acceptMutation.isPending || rejectMutation.isPending
                ? 'Processing...'
                : `Confirm ${actionMode === 'accept' ? 'Accept' : 'Reject'}`}
            </button>
            <button
              onClick={() => {
                setActionMode(null);
                setNotes('');
              }}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={acceptMutation.isPending || rejectMutation.isPending}
              aria-label="Cancel action"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Timestamp */}
      <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
        Requested {format(parseISO(swap.requestedAt), 'MMM d, yyyy h:mm a')}
      </div>
    </div>
  );
}
