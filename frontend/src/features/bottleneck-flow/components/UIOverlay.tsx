/**
 * UI Overlay Component
 *
 * HUD overlay for the bottleneck visualization with:
 * - Title and telemetry header
 * - Lane labels (left side)
 * - Control panel with faculty toggles (right side)
 * - Metrics grid
 * - Legend (bottom left)
 * - Controls hint (bottom right)
 */

'use client';

import React from 'react';
import { RefreshCcw, Activity, GitMerge } from 'lucide-react';
import { LANES, COLORS } from '../constants';
import type { UIOverlayProps } from '../types';

export function UIOverlay({
  metrics,
  simState,
  faculty,
  onToggleFaculty,
  onToggleFix,
  onReset,
}: UIOverlayProps) {
  // Calculate stream volume indicator
  const streamVolume = Math.max(
    0,
    Math.round(100 - (metrics.orphaned + metrics.atRisk) * 5)
  );

  // Determine status banner styling
  let statusClass = 'bg-green-500/20 text-green-500 border-green-500/30';
  let statusText = 'SYSTEM NOMINAL';

  if (metrics.orphaned > 0) {
    statusClass = 'bg-red-500/20 text-red-500 border-red-500/30';
    statusText = `CRITICAL: ${metrics.orphaned} ORPHANED`;
  } else if (metrics.atRisk > 0 || metrics.rerouted > 0) {
    statusClass = 'bg-amber-500/20 text-amber-500 border-amber-500/30';
    statusText = `DEGRADED: ${metrics.rerouted + metrics.atRisk} AFFECTED`;
  }

  return (
    <div className="absolute inset-0 pointer-events-none z-10 flex flex-col justify-between p-5">
      {/* HUD Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-green-500 flex items-center gap-2">
          <Activity className="w-6 h-6" />
          BOTTLENECK FLOW
        </h1>
        <p className="text-xs opacity-50 mt-1 uppercase tracking-widest">
          Supervision Cascade Visualization
        </p>
        <div className="mt-4 font-mono text-xs opacity-60">
          STREAM VOLUME: {streamVolume}% | DIVERSIONS:{' '}
          {metrics.rerouted + metrics.atRisk}
        </div>
      </div>

      {/* Lane Labels (Left Side) */}
      <div className="absolute left-6 top-1/2 -translate-y-1/2 flex flex-col gap-24 pointer-events-none">
        {Object.entries(LANES).map(([key, lane]) => (
          <div
            key={key}
            className="[writing-mode:vertical-rl] rotate-180 text-xs font-bold tracking-[0.2em] uppercase opacity-60"
            style={{ color: lane.color }}
          >
            {lane.name}
          </div>
        ))}
      </div>

      {/* Control Panel (Right Side) */}
      <div className="absolute right-6 top-6 w-80 bg-black/60 border border-white/10 backdrop-blur-md rounded-xl p-5 pointer-events-auto shadow-2xl">
        {/* Status Banner */}
        <div
          className={`py-3 px-4 rounded-lg text-xs font-bold uppercase tracking-wider text-center border mb-4 transition-colors duration-300 ${statusClass}`}
        >
          {statusText}
        </div>

        {/* Toggle Switch */}
        <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg mb-4">
          <span className="text-xs font-medium flex items-center gap-2 text-white">
            <GitMerge className="w-4 h-4 text-blue-400" />
            Show Suggested Fix
          </span>
          <button
            onClick={onToggleFix}
            className={`relative w-11 h-6 rounded-full transition-colors duration-200 ease-in-out focus:outline-none ${
              simState.showSuggestedFix ? 'bg-green-500' : 'bg-white/10'
            }`}
          >
            <span
              className={`inline-block w-5 h-5 transform bg-white rounded-full transition-transform duration-200 ease-in-out translate-y-0.5 ${
                simState.showSuggestedFix ? 'translate-x-5' : 'translate-x-0.5'
              }`}
            />
          </button>
        </div>

        {/* Faculty List */}
        <div className="text-[10px] font-bold uppercase tracking-widest opacity-50 mb-2 text-white">
          Faculty Status (Click to Disable)
        </div>
        <div className="max-h-64 overflow-y-auto space-y-1.5 mb-4 pr-1">
          {faculty.map((f) => {
            const isDisabled = simState.disabledFacultyIds.has(f.id);
            const lane = LANES[f.lane];
            return (
              <button
                key={f.id}
                onClick={() => onToggleFaculty(f.id)}
                className={`w-full flex items-center p-2.5 rounded-lg text-left transition-all border ${
                  isDisabled
                    ? 'bg-red-500/10 border-red-500/50'
                    : 'bg-white/5 border-transparent hover:bg-white/10'
                }`}
              >
                <div
                  className="w-2.5 h-2.5 rounded-full mr-3"
                  style={{
                    backgroundColor: isDisabled ? COLORS.critical : lane.color,
                    boxShadow: `0 0 8px ${isDisabled ? COLORS.critical : lane.color}`,
                  }}
                />
                <div className="flex-1 min-w-0">
                  <div
                    className={`text-xs font-medium truncate text-white ${
                      isDisabled ? 'line-through opacity-50' : ''
                    }`}
                  >
                    {f.name}
                  </div>
                  <div className="text-[10px] opacity-40 text-white">
                    {f.specialty}
                  </div>
                </div>
                <div className="text-[10px] bg-white/10 px-2 py-0.5 rounded-full opacity-60 text-white">
                  {f.traineeIds.length}
                </div>
              </button>
            );
          })}
        </div>

        {/* Reset Button */}
        <button
          onClick={onReset}
          className="w-full py-2.5 bg-white/10 hover:bg-white/20 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2"
        >
          <RefreshCcw className="w-3 h-3" />
          Reset Simulation
        </button>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-white/10">
          <MetricBox
            label="Coverage"
            value={`${metrics.coverage}%`}
            color={
              metrics.coverage === 100
                ? COLORS.nominal
                : metrics.coverage > 80
                  ? COLORS.degraded
                  : COLORS.critical
            }
          />
          <MetricBox
            label="Orphaned"
            value={metrics.orphaned}
            color={metrics.orphaned > 0 ? COLORS.critical : undefined}
          />
          <MetricBox label="Rerouted" value={metrics.rerouted} color={COLORS.atLane} />
          <MetricBox
            label="At Risk"
            value={metrics.atRisk}
            color={metrics.atRisk > 0 ? COLORS.degraded : undefined}
          />
        </div>
      </div>

      {/* Legend (Bottom Left) */}
      <div className="absolute bottom-6 left-6 bg-black/60 border border-white/10 backdrop-blur-md rounded-xl p-4 pointer-events-auto">
        <div className="mb-3">
          <div className="text-[10px] font-bold uppercase tracking-widest opacity-50 mb-2 text-white">
            Constraint Status
          </div>
          <LegendItem color={COLORS.nominal} label="Nominal" />
          <LegendItem color={COLORS.degraded} label="Degraded / Rerouted" />
          <LegendItem color={COLORS.critical} label="Critical / Orphaned" />
          <LegendItem color={COLORS.down} label="Offline" border />
        </div>
        <div>
          <div className="text-[10px] font-bold uppercase tracking-widest opacity-50 mb-2 text-white">
            Hierarchy
          </div>
          <div className="flex items-center gap-4 text-xs opacity-80 text-white">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-white/60 rounded-full" /> Faculty
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-white/60 rounded-full" /> Intern
            </div>
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-white/60 rounded-full" /> Resident
            </div>
          </div>
        </div>
      </div>

      {/* Controls Hint (Bottom Right) */}
      <div className="absolute bottom-6 right-6 text-[10px] opacity-30 text-right pointer-events-none text-white">
        Drag to rotate | Scroll to zoom | Shift+Drag to pan
      </div>
    </div>
  );
}

// ============================================================================
// Sub-components
// ============================================================================

interface MetricBoxProps {
  label: string;
  value: string | number;
  color?: string;
}

function MetricBox({ label, value, color }: MetricBoxProps) {
  return (
    <div className="bg-white/5 p-3 rounded-lg text-center">
      <div className="text-lg font-mono font-bold" style={{ color: color || 'white' }}>
        {value}
      </div>
      <div className="text-[9px] uppercase tracking-wider opacity-50 mt-1 text-white">
        {label}
      </div>
    </div>
  );
}

interface LegendItemProps {
  color: string;
  label: string;
  border?: boolean;
}

function LegendItem({ color, label, border }: LegendItemProps) {
  return (
    <div className="flex items-center mb-1.5 text-[11px] opacity-80 text-white">
      <div
        className={`w-3 h-3 rounded-full mr-3 ${border ? 'border border-gray-600' : ''}`}
        style={{
          backgroundColor: color,
          boxShadow: border ? 'none' : `0 0 8px ${color}`,
        }}
      />
      {label}
    </div>
  );
}

export default UIOverlay;
