/**
 * N-1/N-2 Resilience Visualizer
 *
 * Interactive simulation of faculty absences to test schedule resilience.
 * Click faculty members to mark them absent and observe cascade effects.
 *
 * Features:
 * - N-1 mode: Can handle 1 simultaneous absence
 * - N-2 mode: Can handle 2 simultaneous absences
 * - Real-time cascade metrics
 * - Faculty criticality visualization
 * - Real backend data from blast radius zones API
 *
 * @route Part of /admin/labs/resilience
 */

'use client';

import { useState, useCallback, useMemo } from 'react';
import { RotateCcw, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import { FacultyGrid } from './components/FacultyGrid';
import { CascadeMetrics } from './components/CascadeMetrics';
import { ModeSelector } from './components/ModeSelector';
import { computeCascadeMetrics } from './constants';
import { useN1N2Data } from './hooks/useN1N2Data';
import type { N1N2VisualizerProps, ResilienceMode } from './types';

export function N1N2Visualizer({
  className = '',
}: N1N2VisualizerProps): JSX.Element {
  // Fetch real data from backend API
  const {
    faculty,
    isLoading,
    error,
    n1Pass,
    n2Pass,
    totalZones,
    zonesHealthy,
    zonesCritical,
    containmentActive,
    recommendations,
    refetch,
  } = useN1N2Data();

  const [absentFaculty, setAbsentFaculty] = useState<string[]>([]);
  const [mode, setMode] = useState<ResilienceMode>('N-1');

  // Compute metrics based on current state
  const metrics = useMemo(
    () => computeCascadeMetrics(faculty, absentFaculty, mode),
    [faculty, absentFaculty, mode]
  );

  const handleToggleAbsence = useCallback(
    (id: string) => {
      setAbsentFaculty((prev) => {
        if (prev.includes(id)) {
          return prev.filter((fId) => fId !== id);
        }
        const maxAbsences = mode === 'N-1' ? 1 : 2;
        if (prev.length >= maxAbsences) {
          return prev;
        }
        return [...prev, id];
      });
    },
    [mode]
  );

  const handleModeChange = useCallback(
    (newMode: ResilienceMode) => {
      // If switching to N-1 and more than 1 absent, clear extras
      if (newMode === 'N-1' && absentFaculty.length > 1) {
        setAbsentFaculty([absentFaculty[0]]);
      }
      setMode(newMode);
    },
    [absentFaculty]
  );

  const handleReset = useCallback(() => {
    setAbsentFaculty([]);
  }, []);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // Loading state
  if (isLoading) {
    return (
      <div className={`min-h-full bg-slate-900 p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-4" />
            <p className="text-slate-400">Loading resilience data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`min-h-full bg-slate-900 p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-4" />
            <p className="text-red-400 mb-2">Failed to load resilience data</p>
            <p className="text-slate-500 text-sm mb-4">{error.message}</p>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-all"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-full bg-slate-900 p-6 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">
              N-1/N-2 Resilience Simulator
            </h2>
            <p className="text-sm text-slate-400">
              Click zones to simulate absences and observe cascade effects
            </p>
            {/* N-1/N-2 Status Indicators */}
            <div className="flex gap-4 mt-2">
              <div className="flex items-center gap-1.5">
                {n1Pass ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-400" />
                )}
                <span
                  className={`text-xs font-medium ${n1Pass ? 'text-green-400' : 'text-red-400'}`}
                >
                  N-1: {n1Pass ? 'PASS' : 'FAIL'}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                {n2Pass ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                )}
                <span
                  className={`text-xs font-medium ${n2Pass ? 'text-green-400' : 'text-amber-400'}`}
                >
                  N-2: {n2Pass ? 'PASS' : 'FAIL'}
                </span>
              </div>
              <span className="text-xs text-slate-500">
                {zonesHealthy}/{totalZones} zones healthy
                {zonesCritical > 0 && (
                  <span className="text-red-400 ml-1">
                    ({zonesCritical} critical)
                  </span>
                )}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleRefresh}
              className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all bg-slate-700 hover:bg-slate-600 text-white"
              title="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={handleReset}
              disabled={absentFaculty.length === 0}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg transition-all
                ${
                  absentFaculty.length > 0
                    ? 'bg-slate-700 hover:bg-slate-600 text-white'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                }
              `}
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Containment Alert */}
      {containmentActive && (
        <div className="mb-6 p-4 bg-amber-500/20 border border-amber-500/50 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-amber-400" />
            <span className="text-amber-400 font-semibold">
              Containment Active
            </span>
          </div>
          <p className="text-sm text-amber-200/80 mt-1">
            System is in containment mode to prevent cascade failures.
          </p>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Mode Selector & Metrics */}
        <div className="space-y-6">
          <ModeSelector
            mode={mode}
            onModeChange={handleModeChange}
            absentCount={absentFaculty.length}
          />
          <CascadeMetrics metrics={metrics} mode={mode} />
        </div>

        {/* Right: Faculty Grid */}
        <div className="lg:col-span-2">
          <FacultyGrid
            faculty={faculty}
            absentFaculty={absentFaculty}
            mode={mode}
            onToggleAbsence={handleToggleAbsence}
          />
        </div>
      </div>

      {/* Info Panel */}
      <div className="mt-6 bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-cyan-400 mb-2">
          What is N-1/N-2 Resilience?
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          <strong>N-1 Resilience</strong> means the schedule can absorb a single
          faculty absence without coverage gaps. <strong>N-2 Resilience</strong>{' '}
          means it can handle two simultaneous absences. Military medical
          operations require N-2 resilience for mission-critical coverage.
          Critical zones (red) have the highest cascade impact when understaffed.
        </p>

        {/* Backend Recommendations */}
        {recommendations.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-700">
            <h4 className="text-xs font-semibold text-amber-400 mb-2 uppercase tracking-wide">
              Recommendations
            </h4>
            <ul className="text-xs text-slate-400 space-y-1">
              {recommendations.slice(0, 3).map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-amber-400">-</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default N1N2Visualizer;
