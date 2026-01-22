'use client';

/**
 * MySchedulePanel - User's own weekly schedule (read-only)
 *
 * TODO:
 * - Get current user's personId from auth context
 * - Use FacultyWeeklyEditor with readOnly={true}
 * - Show helpful message about contacting coordinator for changes
 */

import { User, Info } from 'lucide-react';

export function MySchedulePanel() {
  return (
    <div className="space-y-4">
      {/* Info banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-blue-800">
            This is your default weekly activity template. To request changes,
            please contact your program coordinator.
          </p>
        </div>
      </div>

      {/* Placeholder for FacultyWeeklyEditor */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <User className="w-12 h-12 text-blue-400 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-gray-900 mb-2">My Weekly Schedule</h2>
          <p className="text-gray-500 mb-4">
            Your default activity assignments for each day of the week.
          </p>
          <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-amber-100 text-amber-700">
            Component stub - wire up FacultyWeeklyEditor (read-only)
          </div>
        </div>
      </div>
    </div>
  );
}
