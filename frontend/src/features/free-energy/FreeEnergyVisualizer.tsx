'use client';

/**
 * FreeEnergyVisualizer - Schedule Stability Analysis Component
 *
 * Visualizes Helmholtz free energy (F = U - TS) for schedule stability:
 * - Green (F < 0): Schedule is stable and feasible
 * - Yellow (0 ≤ F < 1): Marginal stability with potential issues
 * - Red (F ≥ 1): Unstable configuration with constraint violations
 *
 * Displays:
 * - Energy gauge with color-coded stability indicator
 * - Energy breakdown bar chart (Internal Energy vs Entropy Term)
 * - Human-readable interpretation
 * - List of actionable recommendations
 */

import React from 'react';

interface FreeEnergyResponse {
  freeEnergy: number;
  internalEnergy: number;
  entropyTerm: number;
  temperature: number;
  constraintViolations: number;
  configurationEntropy: number;
  interpretation: string;
  recommendations: string[];
  computedAt: string;
  source: string;
}

export interface FreeEnergyVisualizerProps {
  data: FreeEnergyResponse;
  className?: string;
}

/**
 * Determine color coding based on free energy value
 */
function getEnergyColor(freeEnergy: number): {
  bg: string;
  border: string;
  text: string;
  badge: string;
  status: string;
} {
  if (freeEnergy < 0) {
    return {
      bg: 'from-emerald-900/30 to-teal-900/30',
      border: 'border-emerald-700/50',
      text: 'text-emerald-400',
      badge: 'bg-emerald-900/40 text-emerald-300 border-emerald-700/50',
      status: 'Stable',
    };
  }
  if (freeEnergy < 1) {
    return {
      bg: 'from-yellow-900/30 to-amber-900/30',
      border: 'border-yellow-700/50',
      text: 'text-yellow-400',
      badge: 'bg-yellow-900/40 text-yellow-300 border-yellow-700/50',
      status: 'Marginal',
    };
  }
  return {
    bg: 'from-red-900/30 to-rose-900/30',
    border: 'border-red-700/50',
    text: 'text-red-400',
    badge: 'bg-red-900/40 text-red-300 border-red-700/50',
    status: 'Unstable',
  };
}

/**
 * Calculate the maximum value for bar chart scaling
 */
function getMaxEnergyValue(
  internalEnergy: number,
  entropyTerm: number
): number {
  const max = Math.max(Math.abs(internalEnergy), Math.abs(entropyTerm));
  return Math.max(max * 1.2, 0.1); // Add 20% padding, minimum 0.1
}

/**
 * Format energy values for display
 */
function formatEnergy(value: number): string {
  return value.toFixed(3);
}

/**
 * Format timestamp for display
 */
function formatTimestamp(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return 'Unknown';
  }
}

export function FreeEnergyVisualizer({
  data,
  className = '',
}: FreeEnergyVisualizerProps) {
  const colorScheme = getEnergyColor(data.freeEnergy);
  const maxEnergy = getMaxEnergyValue(data.internalEnergy, data.entropyTerm);

  // Calculate percentage widths for bar chart
  const internalEnergyPercent = Math.abs(
    (data.internalEnergy / maxEnergy) * 100
  );
  const entropyTermPercent = Math.abs((data.entropyTerm / maxEnergy) * 100);

  // Determine bar colors based on values
  const internalEnergyColor =
    data.internalEnergy > 0 ? 'bg-red-600/70' : 'bg-blue-600/70';
  const entropyTermColor =
    data.entropyTerm > 0 ? 'bg-amber-600/70' : 'bg-indigo-600/70';

  return (
    <div
      className={`bg-gradient-to-br ${colorScheme.bg} rounded-lg p-6 border ${colorScheme.border} ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
          <span className="text-lg">⚡</span>
          Free Energy Analysis
        </h3>
        <div className="flex items-center gap-3">
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold border ${colorScheme.badge}`}
          >
            {colorScheme.status}
          </span>
          <span className="text-xs text-gray-500">{formatTimestamp(data.computedAt)}</span>
        </div>
      </div>

      {/* Energy Gauge */}
      <div className="mb-6">
        <div className="flex items-end justify-between mb-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
            Helmholtz Free Energy
          </h4>
          <span className={`text-2xl font-bold ${colorScheme.text}`}>
            {formatEnergy(data.freeEnergy)}
          </span>
        </div>

        {/* Gauge Bar */}
        <div className="relative h-8 bg-gray-900/50 rounded-full border border-gray-700/50 overflow-hidden">
          {/* Scale markers */}
          <div className="absolute inset-0 flex items-center px-2">
            <div className="absolute left-[5%] h-full border-l border-gray-600/30" />
            <div className="absolute left-1/2 h-full border-l border-gray-600/30 transform -translate-x-1/2" />
            <div className="absolute right-[5%] h-full border-l border-gray-600/30" />
          </div>

          {/* Filled portion based on value */}
          <div
            className={`h-full transition-all duration-300 ${colorScheme.text.replace('text-', 'bg-')}`}
            style={{
              width: `${Math.min(Math.max((data.freeEnergy + 2) / 4 * 100, 0), 100)}%`,
            }}
          />

          {/* Scale labels */}
          <div className="absolute inset-0 flex justify-between items-center px-3 pointer-events-none text-xs text-gray-500">
            <span>-2</span>
            <span>0</span>
            <span>2</span>
          </div>
        </div>

        {/* Explanation */}
        <p className="text-xs text-gray-400 mt-2">
          {data.freeEnergy < 0
            ? 'Schedule is stable with feasible constraints'
            : data.freeEnergy < 1
            ? 'Schedule has marginal stability concerns'
            : 'Schedule is unstable with significant constraint violations'}
        </p>
      </div>

      {/* Energy Breakdown */}
      <div className="mb-6">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
          Energy Components
        </h4>

        {/* Internal Energy */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="inline-block w-3 h-3 rounded bg-red-600/70" />
              <span className="text-xs text-gray-300">Internal Energy (U)</span>
            </div>
            <span className="text-xs font-mono text-gray-400">
              {formatEnergy(data.internalEnergy)}
            </span>
          </div>
          <div className="h-6 bg-gray-900/50 rounded border border-gray-700/50 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${internalEnergyColor}`}
              style={{ width: `${internalEnergyPercent}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {data.internalEnergy > 0
              ? `${data.constraintViolations} constraint violations`
              : 'No violations'}
          </p>
        </div>

        {/* Entropy Term */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="inline-block w-3 h-3 rounded bg-amber-600/70" />
              <span className="text-xs text-gray-300">Entropy Term (T·S)</span>
            </div>
            <span className="text-xs font-mono text-gray-400">
              {formatEnergy(data.entropyTerm)}
            </span>
          </div>
          <div className="h-6 bg-gray-900/50 rounded border border-gray-700/50 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${entropyTermColor}`}
              style={{ width: `${entropyTermPercent}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Entropy: {formatEnergy(data.configurationEntropy)} | Temperature:{' '}
            {formatEnergy(data.temperature)}
          </p>
        </div>
      </div>

      {/* Interpretation Panel */}
      <div className="mb-6 p-4 bg-gray-900/40 rounded border border-gray-700/50">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
          Analysis
        </h4>
        <p className="text-sm text-gray-300 leading-relaxed">
          {data.interpretation}
        </p>
      </div>

      {/* Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
            Recommendations
          </h4>
          <ul className="space-y-2">
            {data.recommendations.map((recommendation, index) => (
              <li key={index} className="flex gap-3 text-sm">
                <span className="text-cyan-400 font-bold flex-shrink-0">
                  •
                </span>
                <span className="text-gray-300">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metadata Footer */}
      <div className="mt-6 pt-4 border-t border-gray-700/30">
        <p className="text-xs text-gray-600">
          Source: <span className="text-gray-500 font-mono">{data.source}</span>
        </p>
      </div>
    </div>
  );
}

export default FreeEnergyVisualizer;
