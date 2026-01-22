'use client';

/**
 * MatrixPanel - All-faculty schedule overview (Tier 1+)
 *
 * TODO:
 * - Wrap FacultyMatrixView component
 * - Pass canEdit prop to control click behavior
 * - Week navigator integration
 */

import { Users } from 'lucide-react';

interface MatrixPanelProps {
  canEdit: boolean;
}

export function MatrixPanel({ canEdit }: MatrixPanelProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
      <div className="text-center">
        <Users className="w-12 h-12 text-amber-400 mx-auto mb-4" />
        <h2 className="text-lg font-medium text-gray-900 mb-2">Faculty Matrix View</h2>
        <p className="text-gray-500 mb-4">
          {canEdit
            ? 'Overview of all faculty schedules. Click any cell to edit.'
            : 'Overview of all faculty schedules.'}
        </p>
        <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-amber-100 text-amber-700">
          Component stub - wire up FacultyMatrixView
        </div>
      </div>
    </div>
  );
}
