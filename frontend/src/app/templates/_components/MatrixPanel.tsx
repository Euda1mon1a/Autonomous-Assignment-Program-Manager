'use client';

/**
 * MatrixPanel - All-faculty schedule overview (Tier 1+)
 *
 * Shows the FacultyMatrixView for at-a-glance overview of all
 * faculty schedules. Click behavior depends on edit permissions.
 */

import { useState, useCallback } from 'react';
import { FacultyMatrixView } from '@/components/FacultyMatrixView';
import { FacultyWeeklyEditor } from '@/components/FacultyWeeklyEditor';
import { useFaculty } from '@/hooks/usePeople';
import type { FacultyRole } from '@/types/faculty-activity';

interface MatrixPanelProps {
  canEdit: boolean;
}

export function MatrixPanel({ canEdit }: MatrixPanelProps) {
  const [selectedFacultyId, setSelectedFacultyId] = useState<string | null>(null);

  // Fetch faculty for lookup when opening editor
  const { data: facultyData } = useFaculty();

  // Get selected faculty details
  const selectedFaculty = facultyData?.items?.find((f) => f.id === selectedFacultyId) ?? null;

  // Handle faculty selection from matrix click
  const handleFacultySelect = useCallback(
    (personId: string) => {
      if (canEdit) {
        setSelectedFacultyId(personId);
      }
    },
    [canEdit]
  );

  // Close editor
  const handleCloseEditor = useCallback(() => {
    setSelectedFacultyId(null);
  }, []);

  return (
    <div className="space-y-4">
      {/* Matrix View */}
      <FacultyMatrixView
        showAdjunctToggle={true}
        showWorkloadBadges={canEdit}
        onFacultySelect={canEdit ? handleFacultySelect : undefined}
      />

      {/* Editor Modal */}
      {selectedFaculty && canEdit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Edit Template: {selectedFaculty.name}
              </h2>
              <button
                onClick={handleCloseEditor}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <div className="p-6">
              <FacultyWeeklyEditor
                personId={selectedFaculty.id}
                personName={selectedFaculty.name}
                facultyRole={(selectedFaculty.facultyRole as FacultyRole) ?? null}
                readOnly={false}
                onClose={handleCloseEditor}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
