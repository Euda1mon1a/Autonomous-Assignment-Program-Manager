'use client';

/**
 * Admin Wellness Analytics
 *
 * Lightweight admin view for wellness participation and engagement metrics.
 *
 * @route /admin/wellness
 */

import Link from 'next/link';
import {
  Activity,
  ArrowLeft,
  Flame,
  Heart,
  TrendingUp,
  Users,
} from 'lucide-react';

import { StatCard } from '@/components/data-display/StatCard';
import { useWellnessAnalytics } from '@/features/wellness/hooks/useWellness';

function formatPercent(value?: number) {
  if (value === undefined || value === null) return '—';
  return `${Math.round(value * 100)}%`;
}

function formatWeeks(value?: number) {
  if (value === undefined || value === null) return '—';
  return `${value}w`;
}

export default function AdminWellnessPage() {
  const { data, isLoading } = useWellnessAnalytics();

  const stats = [
    {
      label: 'Participation Rate',
      value: formatPercent(data?.participationRate),
      icon: <Activity className="h-5 w-5 text-emerald-600" />,
      variant: 'success' as const,
    },
    {
      label: 'Active This Week',
      value: data?.activeThisWeek ?? 0,
      icon: <Users className="h-5 w-5 text-blue-600" />,
    },
    {
      label: 'Responses This Week',
      value: data?.totalResponsesThisWeek ?? 0,
      icon: <TrendingUp className="h-5 w-5 text-purple-600" />,
    },
    {
      label: 'Average Streak',
      value: data ? data.averageStreak.toFixed(1) + 'w' : '—',
      icon: <Flame className="h-5 w-5 text-orange-600" />,
    },
    {
      label: 'Longest Streak',
      value: formatWeeks(data?.longestStreak),
      icon: <Flame className="h-5 w-5 text-rose-600" />,
    },
    {
      label: 'Total Participants',
      value: data?.totalParticipants ?? 0,
      icon: <Heart className="h-5 w-5 text-pink-600" />,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Link
                href="/admin/labs"
                className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900"
              >
                <ArrowLeft className="h-4 w-4" />
                Labs
              </Link>
              <span className="text-xs text-gray-400">/</span>
              <span className="text-sm text-gray-500">Wellness</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Wellness Analytics
            </h1>
            <p className="text-gray-600">
              Participation and engagement metrics for resident wellness.
            </p>
          </div>
          <Link
            href="/admin/labs/wellness"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 bg-white text-sm text-gray-700 hover:bg-gray-100"
          >
            View Synapse Monitor
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {stats.map((stat) => (
            <StatCard
              key={stat.label}
              label={stat.label}
              value={stat.value}
              icon={stat.icon}
              variant={stat.variant}
              loading={isLoading}
            />
          ))}
        </div>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Engagement Details
            </h2>
            <div className="space-y-3 text-sm text-gray-600">
              <div className="flex items-center justify-between">
                <span>Active This Block</span>
                <span className="font-medium text-gray-900">
                  {data?.activeThisBlock ?? '—'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Responses This Block</span>
                <span className="font-medium text-gray-900">
                  {data?.totalResponsesThisBlock ?? '—'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Avg Responses / Person</span>
                <span className="font-medium text-gray-900">
                  {data ? data.averageResponsesPerPerson.toFixed(2) : '—'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Points Earned This Week</span>
                <span className="font-medium text-gray-900">
                  {data?.totalPointsEarnedThisWeek ?? 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Hopfield Positions</span>
                <span className="font-medium text-gray-900">
                  {data?.hopfieldPositionsThisWeek ?? 0}
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Signals (Aggregated)
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-md border border-gray-200 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Burnout
                </p>
                <p className="mt-2 text-2xl font-semibold text-gray-900">
                  {data?.averageBurnoutScore?.toFixed(2) ?? '—'}
                </p>
              </div>
              <div className="rounded-md border border-gray-200 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Stress
                </p>
                <p className="mt-2 text-2xl font-semibold text-gray-900">
                  {data?.averageStressScore?.toFixed(2) ?? '—'}
                </p>
              </div>
              <div className="rounded-md border border-gray-200 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Sleep
                </p>
                <p className="mt-2 text-2xl font-semibold text-gray-900">
                  {data?.averageSleepScore?.toFixed(2) ?? '—'}
                </p>
              </div>
              <div className="rounded-md border border-gray-200 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Basin Depth
                </p>
                <p className="mt-2 text-2xl font-semibold text-gray-900">
                  {data?.averageBasinDepth?.toFixed(2) ?? '—'}
                </p>
              </div>
            </div>
            <p className="mt-4 text-xs text-gray-500">
              All values are aggregated and de-identified. Use these signals to
              guide wellness outreach without exposing individual data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
