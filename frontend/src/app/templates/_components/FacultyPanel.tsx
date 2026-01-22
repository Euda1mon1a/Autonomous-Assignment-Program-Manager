'use client';

/**
 * FacultyPanel - Edit any faculty's weekly template (Tier 1+)
 *
 * TODO:
 * - Faculty selector dropdown (useFaculty hook)
 * - FacultyWeeklyEditor in edit mode
 * - Template vs Week-specific mode toggle
 */

import { Calendar } from 'lucide-react';

export function FacultyPanel() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
      <div className="text-center">
        <Calendar className="w-12 h-12 text-amber-400 mx-auto mb-4" />
        <h2 className="text-lg font-medium text-gray-900 mb-2">Faculty Templates</h2>
        <p className="text-gray-500 mb-4">
          Select a faculty member to view and edit their weekly activity template.
        </p>
        <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-amber-100 text-amber-700">
          Component stub - add faculty selector + FacultyWeeklyEditor
        </div>
      </div>
    </div>
  );
}
