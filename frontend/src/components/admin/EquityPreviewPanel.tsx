'use client';

/**
 * EquityPreviewPanel Component
 *
 * Displays current vs projected call distribution per faculty member,
 * showing the equity impact before confirming a bulk reassignment.
 *
 * Features:
 * - Visual bar chart comparing Sunday vs weekday calls
 * - Improvement score indicator
 * - Per-faculty delta display (who gains/loses calls)
 */
import React, { useMemo } from 'react';
import {
  X,
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  AlertCircle,
  Loader2,
  ChevronRight,
  Scale,
} from 'lucide-react';
import type {
  EquityPreviewResponse,
  FacultyEquityDetail,
} from '@/types/call-assignment';

// ============================================================================
// Types
// ============================================================================

export interface EquityPreviewPanelProps {
  /** Whether the panel is visible */
  isOpen: boolean;
  /** Callback to close the panel */
  onClose: () => void;
  /** Equity preview data from backend */
  previewData: EquityPreviewResponse | null;
  /** Whether the preview is loading */
  isLoading: boolean;
  /** Error message if preview failed */
  error?: string | null;
  /** Callback to confirm the reassignment */
  onConfirm?: () => void;
  /** Whether confirm action is pending */
  isConfirmPending?: boolean;
  /** Target person name for reassignment */
  targetPersonName?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Gets the color class based on improvement score
 */
function getImprovementColor(score: number): string {
  if (score > 0.1) return 'text-emerald-400';
  if (score < -0.1) return 'text-red-400';
  return 'text-amber-400';
}

/**
 * Gets the background color class based on improvement score
 */
function getImprovementBgColor(score: number): string {
  if (score > 0.1) return 'bg-emerald-500/20';
  if (score < -0.1) return 'bg-red-500/20';
  return 'bg-amber-500/20';
}

/**
 * Gets the icon for improvement direction
 */
function ImprovementIcon({ score }: { score: number }) {
  if (score > 0.1) return <TrendingUp className="w-4 h-4" />;
  if (score < -0.1) return <TrendingDown className="w-4 h-4" />;
  return <Minus className="w-4 h-4" />;
}

/**
 * Gets the label for improvement score
 */
function getImprovementLabel(score: number): string {
  if (score > 0.3) return 'Significant improvement';
  if (score > 0.1) return 'Moderate improvement';
  if (score > 0) return 'Slight improvement';
  if (score === 0) return 'No change';
  if (score > -0.1) return 'Slight decrease';
  if (score > -0.3) return 'Moderate decrease';
  return 'Significant decrease';
}

/**
 * Calculates the maximum call count for scaling bars
 */
function getMaxCalls(details: FacultyEquityDetail[]): number {
  return Math.max(
    ...details.flatMap((d) => [
      d.current_total_calls,
      d.projected_total_calls,
    ]),
    1
  );
}

// ============================================================================
// Subcomponents
// ============================================================================

interface FacultyEquityRowProps {
  faculty: FacultyEquityDetail;
  maxCalls: number;
}

function FacultyEquityRow({ faculty, maxCalls }: FacultyEquityRowProps) {
  const hasChange = faculty.delta !== 0;

  return (
    <div className="py-3 border-b border-slate-700/50 last:border-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-white">{faculty.name}</span>
        <div className="flex items-center gap-2">
          {hasChange && (
            <span
              className={`text-xs font-medium ${
                faculty.delta > 0 ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {faculty.delta > 0 ? '+' : ''}
              {faculty.delta}
            </span>
          )}
          <span className="text-xs text-slate-500">
            {faculty.current_total_calls} {'->'} {faculty.projected_total_calls}
          </span>
        </div>
      </div>

      {/* Current distribution bar */}
      <div className="relative h-4 bg-slate-700/50 rounded mb-1">
        <div className="absolute inset-y-0 left-0 flex">
          {/* Sunday calls (current) */}
          <div
            className="h-full bg-blue-500/60 rounded-l"
            style={{
              width: `${(faculty.current_sunday_calls / maxCalls) * 100}%`,
            }}
            title={`Current Sunday: ${faculty.current_sunday_calls}`}
          />
          {/* Weekday calls (current) */}
          <div
            className="h-full bg-emerald-500/60"
            style={{
              width: `${(faculty.current_weekday_calls / maxCalls) * 100}%`,
            }}
            title={`Current Weekday: ${faculty.current_weekday_calls}`}
          />
        </div>
        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-slate-400">
          Current
        </span>
      </div>

      {/* Projected distribution bar */}
      <div className="relative h-4 bg-slate-700/50 rounded">
        <div className="absolute inset-y-0 left-0 flex">
          {/* Sunday calls (projected) */}
          <div
            className={`h-full rounded-l ${
              hasChange ? 'bg-blue-400' : 'bg-blue-500/60'
            }`}
            style={{
              width: `${(faculty.projected_sunday_calls / maxCalls) * 100}%`,
            }}
            title={`Projected Sunday: ${faculty.projected_sunday_calls}`}
          />
          {/* Weekday calls (projected) */}
          <div
            className={`h-full ${hasChange ? 'bg-emerald-400' : 'bg-emerald-500/60'}`}
            style={{
              width: `${(faculty.projected_weekday_calls / maxCalls) * 100}%`,
            }}
            title={`Projected Weekday: ${faculty.projected_weekday_calls}`}
          />
        </div>
        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-slate-400">
          Projected
        </span>
      </div>
    </div>
  );
}

interface StatsSummaryProps {
  label: string;
  current: { min: number; max: number; mean: number; stdev: number };
  projected: { min: number; max: number; mean: number; stdev: number };
}

function StatsSummary({ label, current, projected }: StatsSummaryProps) {
  const stdevDiff = projected.stdev - current.stdev;
  const improved = stdevDiff < 0;

  return (
    <div className="p-3 bg-slate-700/30 rounded-lg">
      <h4 className="text-xs font-medium text-slate-400 mb-2">{label}</h4>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-slate-500">Range:</span>
          <span className="ml-1 text-slate-300">
            {current.min}-{current.max}
          </span>
          <ChevronRight className="inline w-3 h-3 text-slate-600 mx-1" />
          <span
            className={
              projected.max - projected.min < current.max - current.min
                ? 'text-emerald-400'
                : 'text-slate-300'
            }
          >
            {projected.min}-{projected.max}
          </span>
        </div>
        <div>
          <span className="text-slate-500">StdDev:</span>
          <span className="ml-1 text-slate-300">{current.stdev.toFixed(2)}</span>
          <ChevronRight className="inline w-3 h-3 text-slate-600 mx-1" />
          <span className={improved ? 'text-emerald-400' : 'text-red-400'}>
            {projected.stdev.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function EquityPreviewPanel({
  isOpen,
  onClose,
  previewData,
  isLoading,
  error,
  onConfirm,
  isConfirmPending,
  targetPersonName,
}: EquityPreviewPanelProps) {
  // Sort faculty by absolute delta (most affected first)
  const sortedFacultyDetails = useMemo(() => {
    if (!previewData?.faculty_details) return [];
    return [...previewData.faculty_details].sort(
      (a, b) => Math.abs(b.delta) - Math.abs(a.delta)
    );
  }, [previewData?.faculty_details]);

  const maxCalls = useMemo(
    () => getMaxCalls(sortedFacultyDetails),
    [sortedFacultyDetails]
  );

  // Count affected faculty
  const affectedCount = useMemo(
    () => sortedFacultyDetails.filter((f) => f.delta !== 0).length,
    [sortedFacultyDetails]
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-violet-500/20 rounded-lg">
              <Scale className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">
                Equity Impact Preview
              </h2>
              <p className="text-sm text-slate-400">
                {targetPersonName
                  ? `Reassigning to ${targetPersonName}`
                  : 'Preview call distribution changes'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isConfirmPending}
            className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
              <span className="ml-3 text-slate-400">Calculating equity impact...</span>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="p-6">
              <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <div>
                  <p className="text-sm font-medium text-red-400">
                    Failed to load equity preview
                  </p>
                  <p className="text-xs text-red-400/80">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Preview Data */}
          {previewData && !isLoading && !error && (
            <div className="p-6 space-y-6">
              {/* Improvement Score Banner */}
              <div
                className={`flex items-center justify-between p-4 rounded-lg ${getImprovementBgColor(
                  previewData.improvement_score
                )}`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-lg bg-slate-800/50 ${getImprovementColor(
                      previewData.improvement_score
                    )}`}
                  >
                    <ImprovementIcon score={previewData.improvement_score} />
                  </div>
                  <div>
                    <p
                      className={`text-sm font-medium ${getImprovementColor(
                        previewData.improvement_score
                      )}`}
                    >
                      {getImprovementLabel(previewData.improvement_score)}
                    </p>
                    <p className="text-xs text-slate-400">
                      Equity score change: {previewData.improvement_score > 0 ? '+' : ''}
                      {(previewData.improvement_score * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-400">Affected faculty</p>
                  <p className="text-lg font-semibold text-white">
                    {affectedCount}
                  </p>
                </div>
              </div>

              {/* Stats Comparison */}
              <div className="grid grid-cols-2 gap-4">
                <StatsSummary
                  label="Sunday Calls"
                  current={previewData.current_equity.sunday_call_stats as { min: number; max: number; mean: number; stdev: number }}
                  projected={previewData.projected_equity.sunday_call_stats as { min: number; max: number; mean: number; stdev: number }}
                />
                <StatsSummary
                  label="Weekday Calls"
                  current={previewData.current_equity.weekday_call_stats as { min: number; max: number; mean: number; stdev: number }}
                  projected={previewData.projected_equity.weekday_call_stats as { min: number; max: number; mean: number; stdev: number }}
                />
              </div>

              {/* Legend */}
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-blue-500 rounded" />
                  <span className="text-slate-400">Sunday calls</span>
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-emerald-500 rounded" />
                  <span className="text-slate-400">Weekday calls</span>
                </span>
              </div>

              {/* Faculty Distribution */}
              <div>
                <h3 className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
                  <Users className="w-4 h-4" />
                  Per-Faculty Distribution
                </h3>
                <div className="bg-slate-700/30 rounded-lg px-4">
                  {sortedFacultyDetails.length > 0 ? (
                    sortedFacultyDetails.map((faculty) => (
                      <FacultyEquityRow
                        key={faculty.personId}
                        faculty={faculty}
                        maxCalls={maxCalls}
                      />
                    ))
                  ) : (
                    <div className="py-8 text-center text-slate-400">
                      No faculty data available
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-700 bg-slate-900/50">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Lower standard deviation = more equitable distribution
            </p>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                disabled={isConfirmPending}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              {onConfirm && (
                <button
                  onClick={onConfirm}
                  disabled={isConfirmPending || isLoading || !!error}
                  className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isConfirmPending && <Loader2 className="w-4 h-4 animate-spin" />}
                  Confirm Reassignment
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EquityPreviewPanel;
