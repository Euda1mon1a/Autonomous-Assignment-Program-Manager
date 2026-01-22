'use client';

/**
 * RotationsPanel - Rotation templates list with view/edit modes
 *
 * TODO: Wire up existing components from /admin/rotations
 * - TemplateTable for list view
 * - Search/filter functionality
 * - Create/Edit modals for Tier 1+
 */

import { LayoutTemplate } from 'lucide-react';

interface RotationsPanelProps {
  canEdit: boolean;
}

export function RotationsPanel({ canEdit }: RotationsPanelProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
      <div className="text-center">
        <LayoutTemplate className="w-12 h-12 text-violet-400 mx-auto mb-4" />
        <h2 className="text-lg font-medium text-gray-900 mb-2">Rotation Templates</h2>
        <p className="text-gray-500 mb-4">
          {canEdit
            ? 'View and edit rotation scheduling patterns.'
            : 'View rotation scheduling patterns. Contact a coordinator to make changes.'}
        </p>
        <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-amber-100 text-amber-700">
          Component stub - wire up TemplateTable from /admin/rotations
        </div>
      </div>
    </div>
  );
}
