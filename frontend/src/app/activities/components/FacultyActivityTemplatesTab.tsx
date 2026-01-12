'use client';

/**
 * Faculty Activity Templates Tab Component
 *
 * Displays the faculty activity matrix for managing weekly activity patterns.
 * This integrates the FacultyMatrixView component with permission-based controls.
 *
 * Features:
 * - All-faculty matrix view with week navigation
 * - Per-faculty editor modal (template vs week-specific mode)
 * - Role filtering and adjunct toggle
 * - Activity legend with color coding
 *
 * Permission-gated actions:
 * - Tier 0: View only
 * - Tier 1: Edit templates and overrides
 * - Tier 2: Full access including bulk operations
 */

import { Info, Lock } from 'lucide-react';
import { FacultyMatrixView } from '@/components/FacultyMatrixView';

// ============================================================================
// Types
// ============================================================================

export interface FacultyActivityTemplatesTabProps {
  /** Whether the user can create/edit templates */
  canEdit: boolean;
  /** Whether the user can delete templates */
  canDelete: boolean;
}

// ============================================================================
// Read-Only Banner Component
// ============================================================================

function ReadOnlyBanner() {
  return (
    <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
      <div className="flex items-start gap-3">
        <Lock className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
        <div>
          <h3 className="font-semibold text-amber-900 mb-1">View-Only Mode</h3>
          <p className="text-sm text-amber-800">
            You can view faculty activity templates but cannot make changes.
            Contact an administrator or program coordinator to request edit access.
          </p>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Activity Legend Component
// ============================================================================

function ActivityLegend() {
  const legendItems = [
    { color: 'bg-blue-500', label: 'AT - Attending Time (Supervision)' },
    { color: 'bg-green-500', label: 'FM Clinic - Family Medicine' },
    { color: 'bg-purple-500', label: 'GME - Graduate Medical Ed' },
    { color: 'bg-indigo-500', label: 'DFM - Dept Family Medicine' },
    { color: 'bg-amber-500', label: 'PCAT - Post-Call Attending (Supervision)' },
    { color: 'bg-teal-500', label: 'DO - Direct Observation (Supervision)' },
    { color: 'bg-emerald-500', label: 'SM Clinic - Sports Medicine' },
    { color: 'border border-amber-400', label: 'Locked slot (HARD constraint)' },
  ];

  return (
    <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Activity Legend</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {legendItems.map((item, index) => (
          <div key={index} className="flex items-center gap-2 text-sm text-gray-600">
            <div className={`w-4 h-4 ${item.color} rounded flex-shrink-0`} />
            <span>{item.label}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 pt-3 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          <strong>Role permissions:</strong> PD (GME only), APD (GME + FM Clinic), OIC (DFM + GME + FM Clinic),
          Dept Chief (DFM + FM Clinic), Sports Med (SM Clinic), Core (GME + FM Clinic)
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Usage Instructions Component
// ============================================================================

function UsageInstructions({ canEdit }: { canEdit: boolean }) {
  if (!canEdit) return null;

  return (
    <div className="mb-6 p-4 bg-slate-50 border border-slate-200 rounded-lg">
      <div className="flex items-start gap-3">
        <Info className="w-5 h-5 text-slate-600 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-slate-700">
          <p className="font-medium text-slate-900 mb-2">How to use this view:</p>
          <ul className="list-disc list-inside space-y-1 text-slate-600">
            <li>Click any cell in the matrix to open the faculty editor</li>
            <li><strong>Template mode:</strong> Edit the default weekly pattern (applies every week)</li>
            <li><strong>Week mode:</strong> Create overrides for specific weeks</li>
            <li>Use <kbd className="px-1.5 py-0.5 bg-slate-200 rounded text-xs">Shift+Click</kbd> to toggle locked slots (HARD constraints)</li>
            <li>Activities are filtered by faculty role permissions</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Tab Component
// ============================================================================

export function FacultyActivityTemplatesTab({ canEdit, canDelete: _canDelete }: FacultyActivityTemplatesTabProps) {
  const handleFacultySelect = (_personId: string) => {
    // The FacultyMatrixView handles opening its own editor modal
    // This callback is for tracking purposes or parent component coordination
  };

  return (
    <div>
      {/* Read-only banner for Tier 0 users */}
      {!canEdit && <ReadOnlyBanner />}

      {/* Usage instructions for editors */}
      <UsageInstructions canEdit={canEdit} />

      {/* Faculty Matrix View */}
      <div className="bg-slate-900 rounded-lg overflow-hidden">
        <FacultyMatrixView
          showAdjunctToggle={true}
          onFacultySelect={handleFacultySelect}
          showWorkloadBadges={canEdit}
        />
      </div>

      {/* Activity Legend */}
      <ActivityLegend />
    </div>
  );
}
