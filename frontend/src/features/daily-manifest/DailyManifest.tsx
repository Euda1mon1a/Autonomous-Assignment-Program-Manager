'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { Calendar, RefreshCw, AlertCircle, Search, CalendarX, Info } from 'lucide-react';
import { SituationalAwareness } from './SituationalAwareness';
import { ClinicCoverageTable } from './ClinicCoverageTable';
import { useDailyManifestV2 } from './hooks';

/**
 * Daily Manifest - V2 Redesign
 *
 * Designed for nursing staff and front desk to quickly see:
 * - WHO is NOT in clinic (FMIT, nights, remote)
 * - Who the ATTENDING is for AM/PM
 * - WHO is IN clinic (by location, both AM and PM)
 *
 * Key changes from V1:
 * - No AM/PM toggle - shows both
 * - Situational awareness at top
 * - Table layout for clinic coverage
 */
export function DailyManifest() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [searchQuery, setSearchQuery] = useState('');

  const dateString = format(selectedDate, 'yyyy-MM-dd');

  const { data, isLoading, isError, error, refetch, isFetching } =
    useDailyManifestV2(dateString);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">FM Clinic Manifest</h1>
          <p className="text-gray-600">
            Who&apos;s in clinic today - For nursing staff and front desk
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Refresh"
          >
            <RefreshCw
              className={`w-5 h-5 text-gray-600 ${isFetching ? 'animate-spin' : ''}`}
            />
          </button>
        </div>
      </div>

      {/* Controls - simplified: just date and search */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-4">
          {/* Date Picker */}
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <input
              type="date"
              value={format(selectedDate, 'yyyy-MM-dd')}
              onChange={(e) => setSelectedDate(new Date(e.target.value))}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={() => setSelectedDate(new Date())}
              className="px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              Today
            </button>
          </div>

          {/* Search */}
          <div className="flex-1 min-w-[200px] max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search locations or people..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Last updated */}
          {data?.generated_at && (
            <div className="text-xs text-gray-500 ml-auto">
              Updated: {format(new Date(data.generated_at), 'h:mm a')}
            </div>
          )}
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-3" />
            <p className="text-gray-600">Loading manifest data...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-red-800 mb-1">
                Unable to Load Manifest
              </h3>
              <p className="text-sm text-red-700">
                {error?.status === 404
                  ? 'The manifest service is temporarily unavailable. Please try again later.'
                  : error?.status === 0
                    ? 'Unable to connect to the server. Please check your network connection.'
                    : error?.message || 'An unexpected error occurred. Please try again.'}
              </p>
            </div>
            <button
              onClick={() => refetch()}
              className="px-3 py-1.5 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      {!isLoading && !isError && data && (
        <>
          {/* Situational Awareness - WHO is NOT in clinic */}
          <SituationalAwareness
            data={data.situational_awareness}
            attending={data.attending}
          />

          {/* FM Clinic Coverage Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              FM Clinic Coverage
              {data.clinic_coverage.length > 0 && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({data.clinic_coverage.length} staff)
                </span>
              )}
            </h2>
          </div>

          {/* Clinic Coverage Table */}
          {data.clinic_coverage.length > 0 ? (
            <ClinicCoverageTable
              locations={data.clinic_coverage}
              searchQuery={searchQuery}
            />
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
              <CalendarX className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Schedule Data for {format(selectedDate, 'MMMM d, yyyy')}
              </h3>
              <p className="text-gray-600 max-w-md mx-auto mb-4">
                There are no staff assignments scheduled for this date.
              </p>

              {/* Info box with helpful guidance */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-lg mx-auto text-left">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-blue-900 mb-1">
                      What you can do:
                    </h4>
                    <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                      <li>Try selecting a different date when schedules are available</li>
                      <li>Contact your program coordinator if you expected to see assignments</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Quick actions */}
              <div className="mt-4 flex items-center justify-center gap-3">
                <button
                  onClick={() => setSelectedDate(new Date())}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
                >
                  Go to Today
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
