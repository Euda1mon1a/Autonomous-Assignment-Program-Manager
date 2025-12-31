/**
 * SwapApprovalPanel Component
 *
 * Panel for coordinators/admins to approve or reject swap requests
 */

import React, { useState } from 'react';
import { Badge } from '../ui/Badge';
import { SwapCard, SwapRequest } from './SwapCard';

export interface SwapApprovalPanelProps {
  pendingSwaps: SwapRequest[];
  onApprove: (swapId: string, notes?: string) => Promise<void>;
  onReject: (swapId: string, reason: string) => Promise<void>;
  className?: string;
}

export const SwapApprovalPanel: React.FC<SwapApprovalPanelProps> = ({
  pendingSwaps,
  onApprove,
  onReject,
  className = '',
}) => {
  const [selectedSwapId, setSelectedSwapId] = useState<string | null>(null);
  const [actionType, setActionType] = useState<'approve' | 'reject' | null>(null);
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const selectedSwap = pendingSwaps.find(s => s.id === selectedSwapId);

  const handleAction = async () => {
    if (!selectedSwapId || !actionType) return;

    setError('');
    setIsSubmitting(true);

    try {
      if (actionType === 'approve') {
        await onApprove(selectedSwapId, notes || undefined);
      } else {
        if (!notes.trim()) {
          setError('Please provide a reason for rejection');
          setIsSubmitting(false);
          return;
        }
        await onReject(selectedSwapId, notes);
      }

      // Reset form
      setSelectedSwapId(null);
      setActionType(null);
      setNotes('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process swap request');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setSelectedSwapId(null);
    setActionType(null);
    setNotes('');
    setError('');
  };

  if (pendingSwaps.length === 0) {
    return (
      <div className={`swap-approval-panel bg-white rounded-lg shadow p-8 text-center ${className}`}>
        <div className="text-4xl mb-3">✅</div>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">All Caught Up!</h3>
        <p className="text-sm text-gray-600">
          No pending swap requests to review
        </p>
      </div>
    );
  }

  return (
    <div className={`swap-approval-panel bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Swap Approvals</h2>
            <p className="text-sm text-gray-600 mt-1">
              {pendingSwaps.length} pending request{pendingSwaps.length !== 1 ? 's' : ''} require review
            </p>
          </div>
          <Badge variant="warning" className="text-lg px-4 py-2">
            {pendingSwaps.length} Pending
          </Badge>
        </div>
      </div>

      {/* Swap List */}
      <div className="divide-y divide-gray-200">
        {pendingSwaps.map((swap) => {
          const isSelected = selectedSwapId === swap.id;

          return (
            <div
              key={swap.id}
              className={`p-4 transition-colors ${isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
            >
              <SwapCard
                swap={swap}
                compact={!isSelected}
                onViewDetails={() => setSelectedSwapId(isSelected ? null : swap.id)}
              />

              {isSelected && (
                <div className="mt-4 p-4 bg-white rounded-lg border-2 border-blue-300">
                  {/* Action Selection */}
                  {!actionType && (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-lg">Review This Request</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <button
                          onClick={() => setActionType('approve')}
                          className="p-4 border-2 border-green-500 bg-green-50 rounded-lg text-green-900 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
                        >
                          <div className="text-2xl mb-2">👍</div>
                          <div className="font-semibold">Approve Swap</div>
                        </button>
                        <button
                          onClick={() => setActionType('reject')}
                          className="p-4 border-2 border-red-500 bg-red-50 rounded-lg text-red-900 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors"
                        >
                          <div className="text-2xl mb-2">❌</div>
                          <div className="font-semibold">Reject Swap</div>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Approval/Rejection Form */}
                  {actionType && (
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{actionType === 'approve' ? '👍' : '❌'}</span>
                        <h4 className="font-semibold text-lg">
                          {actionType === 'approve' ? 'Approve Swap Request' : 'Reject Swap Request'}
                        </h4>
                      </div>

                      {error && (
                        <div className="p-3 bg-red-50 border border-red-300 rounded text-red-800 text-sm">
                          {error}
                        </div>
                      )}

                      <div>
                        <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
                          {actionType === 'approve' ? 'Notes (Optional)' : 'Rejection Reason *'}
                        </label>
                        <textarea
                          id="notes"
                          value={notes}
                          onChange={(e) => setNotes(e.target.value)}
                          rows={4}
                          placeholder={
                            actionType === 'approve'
                              ? 'Add any notes about this approval...'
                              : 'Please provide a reason for rejection...'
                          }
                          className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>

                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={handleCancel}
                          disabled={isSubmitting}
                          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleAction}
                          disabled={isSubmitting}
                          className={`
                            px-6 py-2 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed
                            ${actionType === 'approve'
                              ? 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500'
                              : 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
                            }
                          `}
                        >
                          {isSubmitting
                            ? 'Processing...'
                            : actionType === 'approve'
                            ? 'Approve Swap'
                            : 'Reject Swap'
                          }
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SwapApprovalPanel;
