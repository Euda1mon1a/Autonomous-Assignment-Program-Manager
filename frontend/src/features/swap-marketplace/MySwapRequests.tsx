'use client';

/**
 * MySwapRequests Component
 *
 * Displays the current user's swap requests organized by
 * incoming requests (to accept/reject) and outgoing requests
 * (pending responses or cancellable).
 */

import { useState } from 'react';
import {
  Inbox,
  Send,
  History,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useMySwapRequests } from './hooks';
import { SwapRequestCard } from './SwapRequestCard';
import type { MyRequestsTab } from './types';

// ============================================================================
// Component
// ============================================================================

export function MySwapRequests() {
  const [activeTab, setActiveTab] = useState<MyRequestsTab>('incoming');
  const { user } = useAuth();
  const { data, isLoading, error, refetch } = useMySwapRequests(user?.id);

  const handleActionComplete = () => {
    refetch();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        <span className="ml-3 text-gray-600">Loading your swap requests...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-lg font-semibold text-red-900 mb-1">
              Error Loading Swap Requests
            </h3>
            <p className="text-red-700">{error.message}</p>
            <button
              onClick={() => refetch()}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const incomingCount = data?.incomingRequests.length || 0;
  const outgoingCount = data?.outgoingRequests.length || 0;
  const recentCount = data?.recentSwaps.length || 0;

  const tabs: Array<{
    id: MyRequestsTab | 'recent';
    label: string;
    icon: typeof Inbox;
    count: number;
  }> = [
    { id: 'incoming', label: 'Incoming', icon: Inbox, count: incomingCount },
    { id: 'outgoing', label: 'Outgoing', icon: Send, count: outgoingCount },
    { id: 'recent', label: 'Recent', icon: History, count: recentCount },
  ];

  const renderTabContent = () => {
    if (activeTab === 'incoming') {
      if (incomingCount === 0) {
        return (
          <div className="text-center py-12">
            <Inbox className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No Incoming Requests
            </h3>
            <p className="text-gray-600">
              You don't have any pending swap requests directed to you.
            </p>
          </div>
        );
      }

      return (
        <div>
          <div className="mb-4">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900">
              Incoming Requests ({incomingCount})
            </h3>
            <p className="text-xs sm:text-sm text-gray-600">
              Swap requests from other faculty members that you can accept or reject
            </p>
          </div>
          <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {data?.incomingRequests.map((swap) => (
              <SwapRequestCard
                key={swap.id}
                swap={swap}
                onActionComplete={handleActionComplete}
              />
            ))}
          </div>
        </div>
      );
    }

    if (activeTab === 'outgoing') {
      if (outgoingCount === 0) {
        return (
          <div className="text-center py-12">
            <Send className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No Outgoing Requests
            </h3>
            <p className="text-gray-600">
              You haven't created any swap requests yet.
            </p>
          </div>
        );
      }

      return (
        <div>
          <div className="mb-4">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900">
              Outgoing Requests ({outgoingCount})
            </h3>
            <p className="text-xs sm:text-sm text-gray-600">
              Swap requests you've created that are awaiting response
            </p>
          </div>
          <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {data?.outgoingRequests.map((swap) => (
              <SwapRequestCard
                key={swap.id}
                swap={swap}
                onActionComplete={handleActionComplete}
              />
            ))}
          </div>
        </div>
      );
    }

    // Recent swaps
    if (recentCount === 0) {
      return (
        <div className="text-center py-12">
          <History className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Recent Swaps
          </h3>
          <p className="text-gray-600">
            You don't have any recently completed or rejected swaps.
          </p>
        </div>
      );
    }

    return (
      <div>
        <div className="mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900">
            Recent Swaps ({recentCount})
          </h3>
          <p className="text-xs sm:text-sm text-gray-600">
            Recently completed, rejected, or cancelled swap requests
          </p>
        </div>
        <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {data?.recentSwaps.map((swap) => (
            <SwapRequestCard
              key={swap.id}
              swap={swap}
              onActionComplete={handleActionComplete}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-4 sm:space-x-8 overflow-x-auto" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as MyRequestsTab)}
                className={`
                  flex items-center gap-2 py-4 px-2 sm:px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors
                  ${
                    isActive
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span>{tab.label}</span>
                {tab.count > 0 && (
                  <span
                    className={`
                      ml-1 px-2 py-0.5 text-xs font-medium rounded-full flex-shrink-0
                      ${
                        isActive
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-700'
                      }
                    `}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div>{renderTabContent()}</div>

      {/* Summary Stats */}
      {(incomingCount > 0 || outgoingCount > 0) && (
        <div className="mt-6 p-3 sm:p-4 bg-blue-50 rounded-lg">
          <h4 className="text-xs sm:text-sm font-medium text-blue-900 mb-2">Summary</h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4 text-sm">
            <div>
              <div className="text-base sm:text-lg text-blue-600 font-medium">{incomingCount}</div>
              <div className="text-xs sm:text-sm text-blue-800">Incoming requests</div>
            </div>
            <div>
              <div className="text-base sm:text-lg text-blue-600 font-medium">{outgoingCount}</div>
              <div className="text-xs sm:text-sm text-blue-800">Outgoing requests</div>
            </div>
            <div className="col-span-2 sm:col-span-1">
              <div className="text-base sm:text-lg text-blue-600 font-medium">{recentCount}</div>
              <div className="text-xs sm:text-sm text-blue-800">Recent swaps</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
