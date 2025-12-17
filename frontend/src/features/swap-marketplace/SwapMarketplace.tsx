'use client';

/**
 * SwapMarketplace Component
 *
 * Main page component for the swap marketplace.
 * Integrates browsing available swaps, managing requests,
 * and creating new swap requests.
 */

import { useState } from 'react';
import {
  ShoppingCart,
  List,
  PlusCircle,
  AlertCircle,
  Loader2,
  Package,
} from 'lucide-react';
import { useSwapMarketplace } from './hooks';
import { SwapFilters } from './SwapFilters';
import { SwapRequestCard } from './SwapRequestCard';
import { SwapRequestForm } from './SwapRequestForm';
import { MySwapRequests } from './MySwapRequests';
import type { MarketplaceTab, SwapFilters as Filters } from './types';

// ============================================================================
// Component
// ============================================================================

export function SwapMarketplace() {
  const [activeTab, setActiveTab] = useState<MarketplaceTab>('browse');
  const [filters, setFilters] = useState<Filters>({});

  const { data: marketplaceData, isLoading, error, refetch } = useSwapMarketplace(filters, {
    enabled: activeTab === 'browse',
  });

  const tabs: Array<{
    id: MarketplaceTab;
    label: string;
    icon: typeof ShoppingCart;
    description: string;
  }> = [
    {
      id: 'browse',
      label: 'Browse Swaps',
      icon: ShoppingCart,
      description: 'View available swap opportunities from other faculty',
    },
    {
      id: 'my-requests',
      label: 'My Requests',
      icon: List,
      description: 'Manage your incoming and outgoing swap requests',
    },
    {
      id: 'create',
      label: 'Create Request',
      icon: PlusCircle,
      description: 'Create a new swap request for one of your assigned weeks',
    },
  ];

  const handleCreateSuccess = () => {
    setActiveTab('my-requests');
  };

  const renderTabContent = () => {
    if (activeTab === 'browse') {
      return (
        <div className="space-y-6">
          {/* Filters */}
          <SwapFilters
            filters={filters}
            onFiltersChange={setFilters}
            isLoading={isLoading}
          />

          {/* Marketplace Entries */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              <span className="ml-3 text-gray-600">Loading marketplace...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-lg font-semibold text-red-900 mb-1">
                    Error Loading Marketplace
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
          )}

          {!isLoading && !error && marketplaceData && (
            <>
              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-blue-600">
                    {marketplaceData.total}
                  </div>
                  <div className="text-sm text-blue-800">Available Swaps</div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-600">
                    {marketplaceData.entries.filter((e) => e.isCompatible).length}
                  </div>
                  <div className="text-sm text-green-800">Compatible with You</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-purple-600">
                    {marketplaceData.myPostings}
                  </div>
                  <div className="text-sm text-purple-800">Your Postings</div>
                </div>
              </div>

              {/* Entries Grid */}
              {marketplaceData.entries.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Swaps Available
                  </h3>
                  <p className="text-gray-600 mb-4">
                    There are currently no swap requests in the marketplace.
                  </p>
                  <button
                    onClick={() => setActiveTab('create')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Create a Request
                  </button>
                </div>
              ) : (
                <div>
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Available Swap Requests ({marketplaceData.entries.length})
                    </h3>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {marketplaceData.entries.map((entry) => (
                      <SwapRequestCard
                        key={entry.requestId}
                        marketplaceEntry={entry}
                        onActionComplete={() => refetch()}
                      />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      );
    }

    if (activeTab === 'my-requests') {
      return <MySwapRequests />;
    }

    if (activeTab === 'create') {
      return (
        <SwapRequestForm
          onSuccess={handleCreateSuccess}
          onCancel={() => setActiveTab('browse')}
        />
      );
    }

    return null;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Swap Marketplace</h1>
        <p className="text-gray-600">
          Browse available swap opportunities, manage your requests, and create new swap requests
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    group flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${
                      isActive
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                  title={tab.description}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div>{renderTabContent()}</div>

      {/* Help Section */}
      <div className="mt-12 p-6 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          How the Swap Marketplace Works
        </h3>
        <div className="grid md:grid-cols-3 gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                1
              </div>
              <h4 className="font-medium text-gray-900">Browse & Filter</h4>
            </div>
            <p className="text-sm text-gray-600 ml-10">
              View available swap requests from other faculty members. Filter by date, status,
              and compatibility with your schedule.
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                2
              </div>
              <h4 className="font-medium text-gray-900">Create Request</h4>
            </div>
            <p className="text-sm text-gray-600 ml-10">
              Create a swap request for one of your assigned FMIT weeks. Choose to target
              specific faculty or let the system find candidates.
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                3
              </div>
              <h4 className="font-medium text-gray-900">Accept & Execute</h4>
            </div>
            <p className="text-sm text-gray-600 ml-10">
              Review incoming requests and accept or reject them. Once accepted, the system
              will process the swap and update schedules.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
