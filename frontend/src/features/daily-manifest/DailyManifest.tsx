'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { Calendar, Clock, Users, RefreshCw, AlertCircle, Search } from 'lucide-react';
import { LocationCard } from './LocationCard';
import { useDailyManifest } from './hooks';

// ============================================================================
// Component
// ============================================================================

export function DailyManifest() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [timeOfDay, setTimeOfDay] = useState<'AM' | 'PM' | 'ALL'>('AM');
  const [searchQuery, setSearchQuery] = useState('');

  const dateString = format(selectedDate, 'yyyy-MM-dd');

  const { data, isLoading, isError, error, refetch, isFetching } = useDailyManifest(
    dateString,
    timeOfDay
  );

  // Filter locations based on search query
  const filteredLocations = data?.locations.filter((location) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      location.clinic_location.toLowerCase().includes(query) ||
      location.time_slots.AM?.some((a) =>
        a.person.name.toLowerCase().includes(query)
      ) ||
      location.time_slots.PM?.some((a) =>
        a.person.name.toLowerCase().includes(query)
      )
    );
  });

  // Compute summary from locations (backend returns per-location summaries)
  const summary = data?.locations.reduce(
    (acc, loc) => ({
      total_locations: acc.total_locations + 1,
      total_staff: acc.total_staff + (loc.staffing_summary?.total || 0),
      total_residents: acc.total_residents + (loc.staffing_summary?.residents || 0),
      total_faculty: acc.total_faculty + (loc.staffing_summary?.faculty || 0),
    }),
    { total_locations: 0, total_staff: 0, total_residents: 0, total_faculty: 0 }
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Daily Manifest
          </h1>
          <p className="text-gray-600">
            Where is everyone NOW - Real-time location and assignment tracking
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Refresh"
          >
            <RefreshCw className={`w-5 h-5 text-gray-600 ${isFetching ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Controls */}
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
          </div>

          {/* Time of Day Selector */}
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-500" />
            <select
              value={timeOfDay}
              onChange={(e) => setTimeOfDay(e.target.value as 'AM' | 'PM' | 'ALL')}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="AM">Morning (AM)</option>
              <option value="PM">Afternoon (PM)</option>
              <option value="ALL">All Day</option>
            </select>
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
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Calendar className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Locations</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.total_locations}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Staff</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.total_staff}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Users className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Residents</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.total_residents}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Users className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Faculty</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.total_faculty}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

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
                Error Loading Manifest
              </h3>
              <p className="text-sm text-red-700">
                {error?.message || 'Failed to load daily manifest data'}
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

      {/* Location Cards Grid */}
      {!isLoading && !isError && filteredLocations && (
        <>
          {filteredLocations.length > 0 ? (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Locations ({filteredLocations.length})
                </h2>
                {data?.generated_at && (
                  <p className="text-xs text-gray-500">
                    Last updated: {format(new Date(data.generated_at), 'MMM d, yyyy h:mm a')}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredLocations.map((location, idx) => (
                  <LocationCard
                    key={`${location.clinic_location}-${idx}`}
                    location={location}
                    timeOfDay={timeOfDay}
                  />
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
              <Users className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <h3 className="text-lg font-medium text-gray-900 mb-1">
                No locations found
              </h3>
              <p className="text-gray-600">
                {searchQuery
                  ? 'Try adjusting your search criteria'
                  : 'No assignments scheduled for this date and time'}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
