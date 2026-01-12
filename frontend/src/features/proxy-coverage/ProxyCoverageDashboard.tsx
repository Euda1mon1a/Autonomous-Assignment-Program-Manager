'use client';

import { useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  Calendar,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Users,
  UserCheck,
  Shield,
  TrendingUp,
} from 'lucide-react';
import { useProxyCoverage } from './hooks';
import { ProxyCoverageCard } from './ProxyCoverageCard';
import type { CoverageType, PersonCoverageSummary } from './types';

const TYPE_LABELS: Record<CoverageType, string> = {
  remote_surrogate: 'Remote',
  swap_absorb: 'Absorb',
  swap_exchange: 'Exchange',
  backup_call: 'Backup',
  absence_coverage: 'Absence',
  temporary_proxy: 'Proxy',
};

/**
 * ProxyCoverageDashboard - Who is covering for whom
 *
 * Comprehensive view of all coverage relationships across the scheduling system.
 * Shows active coverage, upcoming coverage, and statistics.
 */
export function ProxyCoverageDashboard() {
  const [selectedDate, setSelectedDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });

  const { data, isLoading, error, refetch, isRefetching } = useProxyCoverage(selectedDate);

  // Date navigation
  const navigateDate = (direction: 'prev' | 'next') => {
    const current = new Date(selectedDate);
    current.setDate(current.getDate() + (direction === 'next' ? 1 : -1));
    setSelectedDate(current.toISOString().split('T')[0]);
  };

  const goToToday = () => {
    setSelectedDate(new Date().toISOString().split('T')[0]);
  };

  // Format date for display
  const formatDisplayDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="animate-pulse space-y-6">
          <div className="h-10 bg-slate-200 rounded w-1/3" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-slate-200 rounded-xl" />
            ))}
          </div>
          <div className="h-64 bg-slate-200 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="p-6 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <div>
            <p className="text-red-700 font-medium">Unable to load coverage data</p>
            <p className="text-red-600 text-sm">{error.message}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { stats } = data;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Proxy Coverage</h1>
          <p className="text-slate-500 mt-1">Who is covering for whom today</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Date Navigation */}
          <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg p-1">
            <button
              onClick={() => navigateDate('prev')}
              className="p-1.5 rounded hover:bg-slate-100 text-slate-600"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={goToToday}
              className="px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded"
            >
              Today
            </button>
            <button
              onClick={() => navigateDate('next')}
              className="p-1.5 rounded hover:bg-slate-100 text-slate-600"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Refresh */}
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="p-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefetching ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Current Date Banner */}
      <div className="flex items-center gap-2 text-slate-600">
        <Calendar className="w-4 h-4" />
        <span className="font-medium">{formatDisplayDate(selectedDate)}</span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <UserCheck className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-green-800">Active Coverage</span>
          </div>
          <p className="text-2xl font-bold text-green-700">{stats.totalActive}</p>
          <p className="text-xs text-green-600 mt-1">relationships today</p>
        </div>

        <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-800">Upcoming</span>
          </div>
          <p className="text-2xl font-bold text-blue-700">{stats.totalScheduled}</p>
          <p className="text-xs text-blue-600 mt-1">next 7 days</p>
        </div>

        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-amber-600" />
            <span className="text-sm font-medium text-amber-800">Top Coverer</span>
          </div>
          {stats.topCoverers.length > 0 ? (
            <>
              <p className="text-lg font-bold text-amber-700 truncate">
                {stats.topCoverers[0].person.name}
              </p>
              <p className="text-xs text-amber-600 mt-1">
                {stats.topCoverers[0].count} coverage{stats.topCoverers[0].count !== 1 && 's'}
              </p>
            </>
          ) : (
            <p className="text-sm text-amber-600">No coverage</p>
          )}
        </div>

        <div className="p-4 bg-purple-50 border border-purple-200 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-5 h-5 text-purple-600" />
            <span className="text-sm font-medium text-purple-800">By Type</span>
          </div>
          <div className="space-y-1">
            {Object.entries(stats.byType).map(([type, count]) => {
              if (count === 0) return null;
              return (
                <div key={type} className="flex items-center justify-between text-xs">
                  <span className="text-purple-700">{TYPE_LABELS[type as CoverageType]}</span>
                  <span className="font-medium text-purple-800">{count}</span>
                </div>
              );
            })}
            {Object.values(stats.byType).every((v) => v === 0) && (
              <p className="text-sm text-purple-600">None</p>
            )}
          </div>
        </div>
      </div>

      {/* Active Coverage Section */}
      <div className="bg-white border border-slate-200 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-slate-600" />
          <h2 className="text-lg font-semibold text-slate-900">Active Coverage Today</h2>
          <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
            {data.activeCoverage.length}
          </span>
        </div>

        {data.activeCoverage.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            <UserCheck className="w-12 h-12 mx-auto mb-3 text-slate-300" />
            <p className="font-medium">No active coverage relationships</p>
            <p className="text-sm">Everyone is covering their own assignments today</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.activeCoverage.map((coverage) => (
              <ProxyCoverageCard key={coverage.id} coverage={coverage} />
            ))}
          </div>
        )}
      </div>

      {/* Upcoming Coverage Section */}
      {data.upcomingCoverage.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-semibold text-slate-900">Upcoming Coverage</h2>
            <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
              {data.upcomingCoverage.length}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.upcomingCoverage.slice(0, 6).map((coverage) => (
              <ProxyCoverageCard key={coverage.id} coverage={coverage} />
            ))}
          </div>

          {data.upcomingCoverage.length > 6 && (
            <p className="text-center text-sm text-slate-500 mt-4">
              + {data.upcomingCoverage.length - 6} more scheduled
            </p>
          )}
        </div>
      )}

      {/* Coverage by Person Section */}
      {data.byCoverer.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-semibold text-slate-900">Coverage by Person</h2>
          </div>

          <div className="space-y-4">
            {data.byCoverer.slice(0, 5).map((summary: PersonCoverageSummary) => (
              <div
                key={summary.person.id}
                className="flex items-center gap-4 p-3 bg-slate-50 rounded-lg"
              >
                <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center">
                  <UserCheck className="w-5 h-5 text-slate-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-900 truncate">{summary.person.name}</p>
                  {summary.person.pgyLevel && (
                    <p className="text-xs text-slate-500">PGY-{summary.person.pgyLevel}</p>
                  )}
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div className="text-center">
                    <p className="font-semibold text-green-700">{summary.providing.length}</p>
                    <p className="text-xs text-slate-500">Providing</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300" />
                  <div className="text-center">
                    <p className="font-semibold text-blue-700">{summary.receiving.length}</p>
                    <p className="text-xs text-slate-500">Receiving</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-xs text-slate-400 text-center">
        Last updated: {new Date(data.generatedAt).toLocaleTimeString()}
      </div>
    </div>
  );
}
