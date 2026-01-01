'use client';

/**
 * SwapMarketplace Component
 *
 * Main page component for the swap marketplace.
 * Integrates browsing available swaps, managing requests,
 * and creating new swap requests.
 */

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
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
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const cardRefs = useRef<Map<number, HTMLDivElement>>(new Map());

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

  // Keyboard navigation for browse tab
  useEffect(() => {
    if (activeTab !== 'browse' || !marketplaceData?.entries.length) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if user is typing in an input field
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;

      const entries = marketplaceData.entries;

      switch (e.key) {
        case 'ArrowDown':
        case 'j':
          e.preventDefault();
          setSelectedIndex(prev => {
            const next = prev < entries.length - 1 ? prev + 1 : prev;
            cardRefs.current.get(next)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return next;
          });
          break;
        case 'ArrowUp':
        case 'k':
          e.preventDefault();
          setSelectedIndex(prev => {
            const next = prev > 0 ? prev - 1 : 0;
            cardRefs.current.get(next)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return next;
          });
          break;
        case 'Escape':
          e.preventDefault();
          setSelectedIndex(-1);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeTab, marketplaceData?.entries.length]);

  // Reset selection when changing tabs or data
  useEffect(() => {
    setSelectedIndex(-1);
  }, [activeTab, filters]);

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
            <div className="flex items-center justify-center py-12" role="status" aria-live="polite">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" aria-hidden="true" />
              <span className="ml-3 text-gray-600">Loading marketplace...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6" role="alert">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <h3 className="text-lg font-semibold text-red-900 mb-1">
                    Error Loading Marketplace
                  </h3>
                  <p className="text-red-700">{error.message}</p>
                  <button
                    onClick={() => refetch()}
                    className="mt-3 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                    aria-label="Retry loading marketplace"
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
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4" role="region" aria-label="Marketplace statistics">
                <div className="bg-blue-50 rounded-lg p-3 sm:p-4">
                  <div className="text-xl sm:text-2xl font-bold text-blue-600" aria-label={`${marketplaceData.total} available swaps`}>
                    {marketplaceData.total}
                  </div>
                  <div className="text-xs sm:text-sm text-blue-800">Available Swaps</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3 sm:p-4">
                  <div className="text-xl sm:text-2xl font-bold text-green-600" aria-label={`${marketplaceData.entries.filter((e) => e.isCompatible).length} compatible swaps`}>
                    {marketplaceData.entries.filter((e) => e.isCompatible).length}
                  </div>
                  <div className="text-xs sm:text-sm text-green-800">Compatible with You</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-3 sm:p-4">
                  <div className="text-xl sm:text-2xl font-bold text-purple-600" aria-label={`${marketplaceData.myPostings} your postings`}>
                    {marketplaceData.myPostings}
                  </div>
                  <div className="text-xs sm:text-sm text-purple-800">Your Postings</div>
                </div>
              </div>

              {/* Entries Grid */}
              {marketplaceData.entries.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" aria-hidden="true" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Swaps Available
                  </h3>
                  <p className="text-gray-600 mb-4">
                    There are currently no swap requests in the marketplace.
                  </p>
                  <button
                    onClick={() => setActiveTab('create')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    aria-label="Create a new swap request"
                  >
                    Create a Request
                  </button>
                </div>
              ) : (
                <div>
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900">
                      Available Swap Requests ({marketplaceData.entries.length})
                    </h3>
                  </div>
                  <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                    {marketplaceData.entries.map((entry, index) => (
                      <div
                        key={entry.requestId}
                        ref={(el) => {
                          if (el) {
                            cardRefs.current.set(index, el);
                          } else {
                            cardRefs.current.delete(index);
                          }
                        }}
                        tabIndex={0}
                        className={`
                          transition-all rounded-lg
                          ${selectedIndex === index ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
                        `}
                        onFocus={() => setSelectedIndex(index)}
                        onClick={() => setSelectedIndex(index)}
                        role="button"
                        aria-label={`Swap request from ${entry.requestingFacultyName}`}
                      >
                        <SwapRequestCard
                          marketplaceEntry={entry}
                          onActionComplete={() => refetch()}
                        />
                      </div>
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
      {/* Page Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Swap Marketplace</h1>
        <p className="text-sm sm:text-base text-gray-600">
          Browse available swap opportunities, manage your requests, and create new swap requests
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-4 sm:space-x-8 overflow-x-auto" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    group flex items-center gap-2 py-4 px-2 sm:px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors
                    ${
                      isActive
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                  role="tab"
                  aria-selected={isActive}
                  aria-label={tab.description}
                  title={tab.description}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.label.split(' ')[0]}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div>{renderTabContent()}</div>

      {/* Help Section */}
      <div className="mt-8 sm:mt-12 p-4 sm:p-6 bg-gray-50 rounded-lg">
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">
          How the Swap Marketplace Works
        </h3>
        <div className="grid gap-4 sm:gap-6 md:grid-cols-3">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                1
              </div>
              <h4 className="font-medium text-gray-900 text-sm sm:text-base">Browse & Filter</h4>
            </div>
            <p className="text-xs sm:text-sm text-gray-600 ml-10">
              View available swap requests from other faculty members. Filter by date, status,
              and compatibility with your schedule.
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                2
              </div>
              <h4 className="font-medium text-gray-900 text-sm sm:text-base">Create Request</h4>
            </div>
            <p className="text-xs sm:text-sm text-gray-600 ml-10">
              Create a swap request for one of your assigned FMIT weeks. Choose to target
              specific faculty or let the system find candidates.
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                3
              </div>
              <h4 className="font-medium text-gray-900 text-sm sm:text-base">Accept & Execute</h4>
            </div>
            <p className="text-xs sm:text-sm text-gray-600 ml-10">
              Review incoming requests and accept or reject them. Once accepted, the system
              will process the swap and update schedules.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
