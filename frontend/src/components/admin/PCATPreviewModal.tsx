'use client';

/**
 * PCATPreviewModal Component
 *
 * Shows a preview of PCAT (Post-Call Attending) and DO (Direct Observation)
 * assignments that will be created before user confirms the operation.
 *
 * For each Sun-Thurs overnight call:
 * - Creates PCAT assignment for next day AM block
 * - Creates DO assignment for next day PM block
 */
import React from 'react';
import {
  X,
  AlertTriangle,
  Loader2,
  Clock,
  Sun,
  Calendar,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface PCATPreviewAssignment {
  /** Original call assignment ID */
  id: string;
  /** Date of the call */
  callDate: string;
  /** Day of week */
  dayOfWeek: string;
  /** Faculty name */
  personName: string;
  /** Whether PCAT will be created */
  willCreatePCAT: boolean;
  /** Whether DO will be created */
  willCreateDO: boolean;
  /** Next day date for PCAT/DO */
  nextDayDate: string;
  /** Warning message if skipped */
  skipReason?: string;
}

export interface PCATPreviewModalProps {
  /** Whether modal is visible */
  isOpen: boolean;
  /** Callback to close modal */
  onClose: () => void;
  /** Callback to confirm and apply PCAT */
  onConfirm: () => void;
  /** Whether the apply operation is pending */
  isPending: boolean;
  /** Preview data for selected assignments */
  previewAssignments: PCATPreviewAssignment[];
  /** Count of assignments that will create PCAT */
  pcatCount: number;
  /** Count of assignments that will create DO */
  doCount: number;
  /** Count of skipped assignments */
  skippedCount: number;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Formats a date string for display
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Gets the day of week from a date string
 */
function getDayOfWeek(dateStr: string): string {
  const days = [
    'Sunday',
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
  ];
  const date = new Date(dateStr + 'T00:00:00');
  return days[date.getDay()];
}

/**
 * Checks if a date is a Sun-Thu (eligible for PCAT)
 */
function isEligibleForPCAT(dateStr: string): boolean {
  const date = new Date(dateStr + 'T00:00:00');
  const day = date.getDay();
  // 0 = Sunday, 4 = Thursday (eligible)
  // 5 = Friday, 6 = Saturday (not eligible - handled by FMIT)
  return day >= 0 && day <= 4;
}

/**
 * Gets the next day date string
 */
function getNextDay(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00');
  date.setDate(date.getDate() + 1);
  return date.toISOString().split('T')[0];
}

// ============================================================================
// Helper Component for creating preview data
// ============================================================================

export function createPCATPreviewData(
  assignments: Array<{
    id: string;
    date: string;
    person_name: string;
  }>
): {
  previewAssignments: PCATPreviewAssignment[];
  pcatCount: number;
  doCount: number;
  skippedCount: number;
} {
  let pcatCount = 0;
  let doCount = 0;
  let skippedCount = 0;

  const previewAssignments = assignments.map((assignment) => {
    const dayOfWeek = getDayOfWeek(assignment.date);
    const isEligible = isEligibleForPCAT(assignment.date);
    const nextDayDate = getNextDay(assignment.date);

    if (isEligible) {
      pcatCount++;
      doCount++;
    } else {
      skippedCount++;
    }

    return {
      id: assignment.id,
      callDate: assignment.date,
      dayOfWeek,
      personName: assignment.person_name,
      willCreatePCAT: isEligible,
      willCreateDO: isEligible,
      nextDayDate,
      skipReason: isEligible
        ? undefined
        : 'Friday/Saturday calls handled by FMIT rules',
    };
  });

  return { previewAssignments, pcatCount, doCount, skippedCount };
}

// ============================================================================
// Main Component
// ============================================================================

export function PCATPreviewModal({
  isOpen,
  onClose,
  onConfirm,
  isPending,
  previewAssignments,
  pcatCount,
  doCount,
  skippedCount,
}: PCATPreviewModalProps) {
  if (!isOpen) return null;

  const eligibleAssignments = previewAssignments.filter((a) => a.willCreatePCAT);
  const skippedAssignments = previewAssignments.filter((a) => !a.willCreatePCAT);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Clock className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">
                Preview PCAT/DO Assignments
              </h2>
              <p className="text-sm text-slate-400">
                Review what will be created before confirming
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isPending}
            className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Summary Stats */}
        <div className="px-6 py-4 bg-slate-900/50 border-b border-slate-700">
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <Sun className="w-4 h-4 text-amber-400" />
              <span className="text-sm text-slate-400">PCAT (AM):</span>
              <span className="text-sm font-medium text-white">{pcatCount}</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-slate-400">DO (PM):</span>
              <span className="text-sm font-medium text-white">{doCount}</span>
            </div>
            {skippedCount > 0 && (
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-400" />
                <span className="text-sm text-slate-400">Skipped:</span>
                <span className="text-sm font-medium text-amber-400">
                  {skippedCount}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Eligible Assignments */}
          {eligibleAssignments.length > 0 && (
            <div className="mb-6">
              <h3 className="flex items-center gap-2 text-sm font-medium text-emerald-400 mb-3">
                <CheckCircle className="w-4 h-4" />
                Assignments to Process ({eligibleAssignments.length})
              </h3>
              <div className="space-y-2">
                {eligibleAssignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg border border-slate-600/50"
                  >
                    <div className="flex items-center gap-4">
                      <div>
                        <p className="text-sm font-medium text-white">
                          {assignment.personName}
                        </p>
                        <p className="text-xs text-slate-400">
                          Call: {formatDate(assignment.callDate)} ({assignment.dayOfWeek})
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/20 text-amber-400 rounded">
                        <Sun className="w-3 h-3" />
                        PCAT AM
                      </div>
                      <span className="text-slate-500">+</span>
                      <div className="flex items-center gap-1 px-2 py-1 bg-blue-500/20 text-blue-400 rounded">
                        <Calendar className="w-3 h-3" />
                        DO PM
                      </div>
                      <span className="text-slate-500">on</span>
                      <span className="text-slate-300">
                        {formatDate(assignment.nextDayDate)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skipped Assignments */}
          {skippedAssignments.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 text-sm font-medium text-amber-400 mb-3">
                <AlertTriangle className="w-4 h-4" />
                Skipped Assignments ({skippedAssignments.length})
              </h3>
              <div className="space-y-2">
                {skippedAssignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg border border-slate-700"
                  >
                    <div>
                      <p className="text-sm font-medium text-slate-400">
                        {assignment.personName}
                      </p>
                      <p className="text-xs text-slate-500">
                        Call: {formatDate(assignment.callDate)} ({assignment.dayOfWeek})
                      </p>
                    </div>
                    <div className="text-xs text-amber-400/80">
                      {assignment.skipReason}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {previewAssignments.length === 0 && (
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No assignments selected</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-700 bg-slate-900/50">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">
              PCAT = Post-Call Attending (AM block) | DO = Direct Observation (PM block)
            </p>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                disabled={isPending}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={onConfirm}
                disabled={isPending || pcatCount === 0}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                Apply PCAT Rules ({pcatCount} assignments)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PCATPreviewModal;
