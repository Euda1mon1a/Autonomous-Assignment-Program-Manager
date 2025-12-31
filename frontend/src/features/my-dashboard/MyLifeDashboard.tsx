'use client';

/**
 * MyLifeDashboard Component
 *
 * Main dashboard component for residents to view their personal schedule.
 * Displays upcoming assignments, pending swap requests, summary statistics,
 * and provides calendar sync functionality.
 *
 * Mobile-friendly design with responsive layouts and touch-friendly controls.
 */

import { useState } from 'react';
import {
  Calendar,
  Briefcase,
  ArrowRightLeft,
  RefreshCw,
  ChevronDown,
  AlertCircle,
} from 'lucide-react';
import { SummaryCard } from './SummaryCard';
import { UpcomingSchedule } from './UpcomingSchedule';
import { PendingSwaps } from './PendingSwaps';
import { CalendarSync } from './CalendarSync';
import { useMyDashboard } from './hooks';
import { DEFAULT_DAYS_AHEAD } from './types';

// ============================================================================
// Types
// ============================================================================

interface MyLifeDashboardProps {
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function MyLifeDashboard({ className = '' }: MyLifeDashboardProps) {
  const [daysAhead, setDaysAhead] = useState(DEFAULT_DAYS_AHEAD);
  const [showDaysSelector, setShowDaysSelector] = useState(false);

  const {
    data: dashboardData,
    isLoading,
    isError,
    error,
    refetch,
    isRefetching,
  } = useMyDashboard({ daysAhead });

  // Quick day range options
  const dayOptions = [7, 14, 30, 60, 90];

  const handleRefresh = () => {
    refetch();
  };

  const handleSwapRequested = () => {
    // Refresh dashboard when a swap is requested
    refetch();
  };

  const handleSwapAction = (swapId: string) => {
    // Navigate to swap marketplace or show swap details
    // console.log('Handle swap action for:', swapId);
    // For now, just refresh
    refetch();
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">My Schedule</h1>
          {dashboardData?.user && (
            <p className="text-sm text-gray-600 mt-1">
              {dashboardData.user.name} • {dashboardData.user.role}
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isRefetching}
          >
            <RefreshCw className={`w-5 h-5 ${isRefetching ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          <CalendarSync />
        </div>
      </header>

      {/* Error State */}
      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-red-900 mb-1">Failed to load dashboard</h3>
            <p className="text-sm text-red-700">{error?.message}</p>
            <button
              onClick={handleRefresh}
              className="mt-2 text-sm font-medium text-red-600 hover:text-red-700 underline"
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <SummaryCard
          title="Next Assignment"
          value={dashboardData?.summary.nextAssignment || 'None scheduled'}
          icon={Calendar}
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
          isLoading={isLoading}
        />
        <SummaryCard
          title="Workload (4 weeks)"
          value={dashboardData?.summary.workloadNext4Weeks ?? 0}
          icon={Briefcase}
          iconColor="text-green-600"
          bgColor="bg-green-50"
          description="shifts ahead"
          isLoading={isLoading}
        />
        <SummaryCard
          title="Pending Swaps"
          value={dashboardData?.summary.pendingSwapCount ?? 0}
          icon={ArrowRightLeft}
          iconColor="text-purple-600"
          bgColor="bg-purple-50"
          description="requiring action"
          isLoading={isLoading}
        />
      </div>

      {/* Days Ahead Selector */}
      <div className="flex items-center justify-between bg-gray-50 rounded-lg p-4">
        <div className="text-sm text-gray-700">
          <span className="font-medium">Viewing schedule for next</span>{' '}
          <button
            onClick={() => setShowDaysSelector(!showDaysSelector)}
            className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-gray-300 rounded font-semibold text-blue-600 hover:bg-gray-50 transition-colors"
          >
            {daysAhead} days
            <ChevronDown className={`w-4 h-4 transition-transform ${showDaysSelector ? 'rotate-180' : ''}`} />
          </button>
        </div>
        {showDaysSelector && (
          <div className="absolute mt-24 bg-white border border-gray-200 rounded-lg shadow-lg p-2 z-10">
            {dayOptions.map((days) => (
              <button
                key={days}
                onClick={() => {
                  setDaysAhead(days);
                  setShowDaysSelector(false);
                }}
                className={`block w-full text-left px-4 py-2 rounded text-sm transition-colors ${
                  days === daysAhead
                    ? 'bg-blue-100 text-blue-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {days} days
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Upcoming Assignments Section */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg md:text-xl font-semibold text-gray-900">
            Upcoming Assignments
          </h2>
          <span className="text-sm text-gray-500">
            {dashboardData?.upcomingSchedule?.length || 0} total
          </span>
        </div>
        <UpcomingSchedule
          assignments={dashboardData?.upcomingSchedule || []}
          isLoading={isLoading}
          onSwapRequested={handleSwapRequested}
        />
      </section>

      {/* Pending Swaps Section */}
      {dashboardData?.pendingSwaps && dashboardData.pendingSwaps.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg md:text-xl font-semibold text-gray-900">
              Pending Swap Requests
            </h2>
            <span className="text-sm text-gray-500">
              {dashboardData.pendingSwaps.length} total
            </span>
          </div>
          <PendingSwaps
            swaps={dashboardData.pendingSwaps}
            isLoading={isLoading}
            onSwapAction={handleSwapAction}
          />
        </section>
      )}

      {/* Absences Section (if any) */}
      {dashboardData?.absences && dashboardData.absences.length > 0 && (
        <section className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-amber-900 mb-2">Upcoming Absences</h2>
          <div className="text-sm text-amber-800">
            You have {dashboardData.absences.length} upcoming absence(s). Make sure your
            schedule is covered.
          </div>
        </section>
      )}

      {/* Mobile-Friendly Footer Tip */}
      <div className="sm:hidden bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          <strong>Tip:</strong> Tap "Sync to Calendar" above to add your schedule to your
          phone's calendar app for easy access on the go.
        </p>
      </div>
    </div>
  );
}
