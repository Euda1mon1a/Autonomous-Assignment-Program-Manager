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
 *
 * @route Part of /admin/labs/resilience
 */

'use client';

import { useState, useCallback, useMemo } from 'react';
import { RotateCcw } from 'lucide-react';
import { FacultyGrid } from './components/FacultyGrid';
import { CascadeMetrics } from './components/CascadeMetrics';
import { ModeSelector } from './components/ModeSelector';
import { MOCK_FACULTY, computeCascadeMetrics } from './constants';
import type { N1N2VisualizerProps, ResilienceMode, Faculty } from './types';

export function N1N2Visualizer({
  className = '',
}: N1N2VisualizerProps): JSX.Element {
  const [faculty] = useState<Faculty[]>(MOCK_FACULTY);
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
              Click faculty members to simulate absences and observe cascade effects
            </p>
          </div>
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
          Critical faculty (red) have the highest cascade impact when absent.
        </p>
      </div>
    </div>
  );
}

export default N1N2Visualizer;
