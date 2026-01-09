'use client';

/**
 * Admin Faculty Activities Page
 *
 * Management interface for faculty weekly activity templates and overrides.
 * Features:
 * - All-faculty matrix view with week navigation
 * - Per-faculty editor modal (template vs week-specific mode)
 * - Role filtering and adjunct toggle
 * - Activity legend with color coding
 */

import { useState } from 'react';
import { Users, UserCog, Calendar, RefreshCw, Info } from 'lucide-react';
import { FacultyMatrixView } from '@/components/FacultyMatrixView';
import { FacultyWeeklyEditor } from '@/components/FacultyWeeklyEditor';
import type { FacultyRole } from '@/types/faculty-activity';
import { FACULTY_ROLE_LABELS } from '@/types/faculty-activity';
import { useQueryClient } from '@tanstack/react-query';
import { facultyActivityQueryKeys } from '@/hooks/useFacultyActivities';

// ============================================================================
// Types
// ============================================================================

interface SelectedFaculty {
  personId: string;
  personName: string;
  facultyRole: FacultyRole | null;
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminFacultyActivitiesPage() {
  const queryClient = useQueryClient();

  // State
  const [selectedFaculty, setSelectedFaculty] = useState<SelectedFaculty | null>(null);
  const [showQuickEditor, setShowQuickEditor] = useState(false);

  // Handlers
  const handleRefresh = () => {
    queryClient.invalidateQueries({
      queryKey: facultyActivityQueryKeys.all,
    });
  };

  const handleCloseEditor = () => {
    setSelectedFaculty(null);
    setShowQuickEditor(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">
                  Faculty Activity Templates
                </h1>
                <p className="text-sm text-slate-400">
                  Manage weekly activity patterns and overrides
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={handleRefresh}
                className="p-2 text-slate-400 hover:text-white transition-colors"
                title="Refresh data"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Info Banner */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-start gap-3 p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
          <Info className="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-slate-300">
            <p className="font-medium text-white mb-1">How to use this page:</p>
            <ul className="list-disc list-inside space-y-1 text-slate-400">
              <li>Click any cell in the matrix to open the faculty editor</li>
              <li><strong>Template mode:</strong> Edit the default weekly pattern (applies every week)</li>
              <li><strong>Week mode:</strong> Create overrides for specific weeks</li>
              <li>Use <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-xs">Shift+Click</kbd> to toggle locked slots (HARD constraints)</li>
              <li>Activities are filtered by faculty role permissions</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <FacultyMatrixView
          showAdjunctToggle={true}
          onFacultySelect={(personId) => {
            // This is called when any cell is clicked
            // The FacultyMatrixView handles opening its own editor modal
          }}
        />
      </main>

      {/* Quick Editor Panel (alternative to modal - for future use) */}
      {showQuickEditor && selectedFaculty && (
        <div className="fixed right-0 top-0 bottom-0 w-[500px] z-50 bg-slate-900 border-l border-slate-700 shadow-2xl overflow-y-auto">
          <FacultyWeeklyEditor
            personId={selectedFaculty.personId}
            personName={selectedFaculty.personName}
            facultyRole={selectedFaculty.facultyRole}
            onClose={handleCloseEditor}
          />
        </div>
      )}

      {/* Activity Legend Info */}
      <footer className="max-w-7xl mx-auto px-4 py-6 border-t border-slate-800">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <div className="w-4 h-4 bg-blue-500 rounded" />
            <span>AT - Attending Time (Supervision)</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <div className="w-4 h-4 bg-green-500 rounded" />
            <span>FM Clinic - Family Medicine</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <div className="w-4 h-4 bg-purple-500 rounded" />
            <span>GME - Graduate Medical Ed</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <div className="w-4 h-4 bg-indigo-500 rounded" />
            <span>DFM - Dept Family Medicine</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <div className="w-4 h-4 bg-amber-500 rounded" />
            <span>PCAT - Post-Call Attending (Supervision)</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <div className="w-4 h-4 bg-teal-500 rounded" />
            <span>DO - Direct Observation (Supervision)</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <div className="w-4 h-4 bg-emerald-500 rounded" />
            <span>SM Clinic - Sports Medicine</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <div className="w-4 h-4 border border-amber-400 rounded" />
            <span>Locked slot (HARD constraint)</span>
          </div>
        </div>

        <div className="mt-4 text-xs text-slate-500">
          <p>
            <strong>Role permissions:</strong> PD (GME only), APD (GME + FM Clinic), OIC (DFM + GME + FM Clinic),
            Dept Chief (DFM + FM Clinic), Sports Med (SM Clinic), Core (GME + FM Clinic)
          </p>
        </div>
      </footer>
    </div>
  );
}
