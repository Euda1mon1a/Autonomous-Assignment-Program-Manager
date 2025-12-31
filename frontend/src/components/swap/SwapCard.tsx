/**
 * SwapCard Component
 *
 * Displays a swap request with status and actions
 */

import React from 'react';
import { Badge } from '../ui/Badge';
import { ShiftIndicator } from '../schedule/ShiftIndicator';
import { RotationBadge } from '../schedule/RotationBadge';

export interface SwapRequest {
  id: string;
  swapType: 'one-to-one' | 'absorb' | 'give-away';
  status: 'pending' | 'approved' | 'rejected' | 'cancelled' | 'completed';
  requestor: {
    id: string;
    name: string;
  };
  givingUpBlock: {
    date: string;
    shift: 'AM' | 'PM' | 'Night';
    rotationType: string;
  };
  targetPerson?: {
    id: string;
    name: string;
  };
  targetBlock?: {
    date: string;
    shift: 'AM' | 'PM' | 'Night';
    rotationType: string;
  };
  reason: string;
  notes?: string;
  createdAt: string;
  expiresAt?: string;
}

export interface SwapCardProps {
  swap: SwapRequest;
  currentUserId?: string;
  onAccept?: (swapId: string) => void;
  onReject?: (swapId: string) => void;
  onCancel?: (swapId: string) => void;
  onViewDetails?: (swapId: string) => void;
  compact?: boolean;
  className?: string;
}

const statusConfig = {
  pending: {
    color: 'bg-yellow-100 border-yellow-500 text-yellow-900',
    badge: 'warning' as const,
    icon: '⏳',
    label: 'Pending',
  },
  approved: {
    color: 'bg-blue-100 border-blue-500 text-blue-900',
    badge: 'default' as const,
    icon: '👍',
    label: 'Approved',
  },
  rejected: {
    color: 'bg-red-100 border-red-500 text-red-900',
    badge: 'destructive' as const,
    icon: '❌',
    label: 'Rejected',
  },
  cancelled: {
    color: 'bg-gray-100 border-gray-500 text-gray-900',
    badge: 'default' as const,
    icon: '🚫',
    label: 'Cancelled',
  },
  completed: {
    color: 'bg-green-100 border-green-500 text-green-900',
    badge: 'default' as const,
    icon: '✅',
    label: 'Completed',
  },
};

const typeIcons = {
  'one-to-one': '🔄',
  'absorb': '📥',
  'give-away': '📤',
};

export const SwapCard: React.FC<SwapCardProps> = ({
  swap,
  currentUserId,
  onAccept,
  onReject,
  onCancel,
  onViewDetails,
  compact = false,
  className = '',
}) => {
  const config = statusConfig[swap.status];
  const isRequestor = currentUserId === swap.requestor.id;
  const isTarget = currentUserId === swap.targetPerson?.id;
  const canAccept = isTarget && swap.status === 'pending' && onAccept;
  const canReject = isTarget && swap.status === 'pending' && onReject;
  const canCancel = isRequestor && swap.status === 'pending' && onCancel;

  const daysUntilExpiry = swap.expiresAt
    ? Math.ceil((new Date(swap.expiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : null;

  if (compact) {
    return (
      <div
        className={`swap-card-compact border-l-4 rounded-lg p-3 bg-white shadow-sm ${config.color} ${className}`}
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <span className="text-xl">{typeIcons[swap.swapType]}</span>
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{swap.requestor.name}</div>
              <div className="text-sm text-gray-600 truncate">
                {new Date(swap.givingUpBlock.date).toLocaleDateString()} - {swap.givingUpBlock.shift}
              </div>
            </div>
          </div>
          <Badge variant={config.badge}>{config.label}</Badge>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`swap-card border-l-4 rounded-lg shadow-md bg-white ${config.color} ${className}`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{typeIcons[swap.swapType]}</span>
            <div>
              <h3 className="font-bold text-lg">
                {swap.swapType === 'one-to-one' && 'Swap Request'}
                {swap.swapType === 'absorb' && 'Absorb Request'}
                {swap.swapType === 'give-away' && 'Give Away Request'}
              </h3>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={config.badge}>{config.label}</Badge>
                {isRequestor && <Badge>You Requested</Badge>}
                {isTarget && <Badge variant="default">You're Target</Badge>}
              </div>
            </div>
          </div>
          <span className="text-2xl">{config.icon}</span>
        </div>

        {/* Expiry Warning */}
        {daysUntilExpiry !== null && daysUntilExpiry <= 3 && swap.status === 'pending' && (
          <div className="mt-2 p-2 bg-orange-50 border border-orange-300 rounded text-orange-800 text-sm">
            ⏰ Expires in {daysUntilExpiry} day{daysUntilExpiry !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-4">
        {/* Requestor Block */}
        <div className="mb-4">
          <div className="text-sm text-gray-600 mb-1">
            <strong>{swap.requestor.name}</strong> is giving up:
          </div>
          <div className="bg-gray-50 rounded p-3 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">
                  {new Date(swap.givingUpBlock.date).toLocaleDateString('en-US', {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                  })}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <ShiftIndicator shift={swap.givingUpBlock.shift} size="sm" variant="badge" />
                <RotationBadge rotationType={swap.givingUpBlock.rotationType} size="sm" />
              </div>
            </div>
          </div>
        </div>

        {/* Target Block (for one-to-one) */}
        {swap.swapType === 'one-to-one' && swap.targetPerson && swap.targetBlock && (
          <div className="mb-4">
            <div className="text-center text-gray-500 mb-2">⇅</div>
            <div className="text-sm text-gray-600 mb-1">
              <strong>{swap.targetPerson.name}</strong> would give up:
            </div>
            <div className="bg-gray-50 rounded p-3 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">
                    {new Date(swap.targetBlock.date).toLocaleDateString('en-US', {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <ShiftIndicator shift={swap.targetBlock.shift} size="sm" variant="badge" />
                  <RotationBadge rotationType={swap.targetBlock.rotationType} size="sm" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Reason */}
        <div className="mb-4">
          <div className="text-sm font-medium text-gray-700 mb-1">Reason:</div>
          <div className="text-sm text-gray-600">{swap.reason}</div>
        </div>

        {/* Notes (if any) */}
        {swap.notes && (
          <div className="mb-4">
            <div className="text-sm font-medium text-gray-700 mb-1">Additional Notes:</div>
            <div className="text-sm text-gray-600 bg-gray-50 rounded p-2 border border-gray-200">
              {swap.notes}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="text-xs text-gray-500">
          Requested {new Date(swap.createdAt).toLocaleDateString()}
        </div>
      </div>

      {/* Actions */}
      {(canAccept || canReject || canCancel || onViewDetails) && (
        <div className="p-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between gap-2">
          {onViewDetails && (
            <button
              onClick={() => onViewDetails(swap.id)}
              className="text-sm text-blue-600 hover:text-blue-800 focus:outline-none focus:underline"
            >
              View Details
            </button>
          )}

          <div className="flex gap-2 ml-auto">
            {canCancel && (
              <button
                onClick={() => onCancel(swap.id)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel Request
              </button>
            )}

            {canReject && (
              <button
                onClick={() => onReject(swap.id)}
                className="px-4 py-2 border border-red-300 bg-red-50 text-red-700 rounded hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Reject
              </button>
            )}

            {canAccept && (
              <button
                onClick={() => onAccept(swap.id)}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                Accept Swap
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SwapCard;
