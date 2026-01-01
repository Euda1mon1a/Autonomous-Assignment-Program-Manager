/**
 * BurnoutRtDisplay Component
 *
 * Displays burnout reproduction number (Rt) using epidemiological SIR model
 */

import React from 'react';

export interface BurnoutRtDisplayProps {
  value: number; // Reproduction number
  threshold?: number; // Default 1.0
  trend?: 'increasing' | 'stable' | 'decreasing';
  onDrillDown?: () => void;
  className?: string;
}

export const BurnoutRtDisplay: React.FC<BurnoutRtDisplayProps> = ({
  value,
  threshold = 1.0,
  trend = 'stable',
  onDrillDown,
  className = '',
}) => {
  const isEpidemic = value > threshold;
  const isWarning = value > threshold * 0.9;

  const getStatusConfig = () => {
    if (isEpidemic) return {
      color: 'bg-red-50 border-red-500 text-red-900',
      icon: '🔴',
      label: 'Burnout Spreading',
      description: 'Rt > 1: Burnout is spreading exponentially. Each burned-out person affects multiple others.',
    };
    if (isWarning) return {
      color: 'bg-yellow-50 border-yellow-500 text-yellow-900',
      icon: '🟡',
      label: 'Approaching Epidemic',
      description: 'Rt near 1: System approaching critical transition point.',
    };
    return {
      color: 'bg-green-50 border-green-500 text-green-900',
      icon: '🟢',
      label: 'Burnout Contained',
      description: 'Rt < 1: Burnout is declining. System is recovering.',
    };
  };

  const status = getStatusConfig();

  const trendIcons = {
    increasing: '📈',
    stable: '➡️',
    decreasing: '📉',
  };

  const trendColors = {
    increasing: 'text-red-600',
    stable: 'text-gray-600',
    decreasing: 'text-green-600',
  };

  // Calculate doubling/halving time
  const getTimescale = (rt: number): string => {
    if (rt === 1.0) return 'N/A (equilibrium)';
    const generations = Math.log(2) / Math.log(Math.abs(rt));
    const days = Math.round(generations * 7); // Assuming 7-day generation time
    if (rt > 1) {
      return `Doubles every ${days} days`;
    } else {
      return `Halves every ${days} days`;
    }
  };

  return (
    <div className={`burnout-rt-display ${className}`}>
      {/* Main Display */}
      <div
        className={`border-l-4 rounded-lg p-6 mb-4 ${status.color}`}
        role="status"
        aria-live="polite"
        aria-label="Burnout reproduction number status"
      >
        <div className="flex items-start gap-4">
          <span className="text-4xl" aria-hidden="true">
            {status.icon}
          </span>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-2xl font-bold">Rt = {value.toFixed(2)}</h3>
              <div className={`flex items-center gap-2 ${trendColors[trend]}`}>
                <span className="text-xl" aria-hidden="true">{trendIcons[trend]}</span>
                <span className="text-sm font-medium capitalize">{trend}</span>
              </div>
            </div>

            <div className="font-semibold mb-2">{status.label}</div>
            <p className="text-sm">{status.description}</p>

            {/* Timescale */}
            <div className="mt-3 p-3 bg-white bg-opacity-50 rounded">
              <div className="text-sm">
                <span className="font-medium">Projection: </span>
                {getTimescale(value)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Gauge Visualization */}
      <div
        className="bg-white rounded-lg p-4 border border-gray-200 mb-4"
        role="img"
        aria-label={`Burnout Rt gauge showing ${value.toFixed(2)} on a scale from 0 to 2, with threshold at 1.0`}
      >
        <div className="relative h-8 mb-4">
          {/* Scale */}
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>0.0</span>
            <span className="font-semibold">1.0 (threshold)</span>
            <span>2.0</span>
          </div>

          {/* Bar */}
          <div className="relative w-full h-4 bg-gray-200 rounded-full overflow-hidden">
            {/* Threshold Line */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-gray-600 z-10"
              style={{ left: '50%' }}
              aria-hidden="true"
            />

            {/* Value Indicator */}
            <div
              className={`absolute top-0 bottom-0 w-1 ${
                isEpidemic ? 'bg-red-600' : isWarning ? 'bg-yellow-600' : 'bg-green-600'
              } z-20`}
              style={{ left: `${Math.min((value / 2) * 100, 100)}%` }}
              aria-hidden="true"
            />
          </div>
        </div>

        {/* Legend */}
        <div className="flex justify-between text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-green-500" aria-hidden="true"></div>
            <span>Declining</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-gray-600" aria-hidden="true"></div>
            <span>Equilibrium</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-red-500" aria-hidden="true"></div>
            <span>Spreading</span>
          </div>
        </div>
      </div>

      {/* Interpretation Guide */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <h4 className="font-semibold text-sm mb-3">Interpretation Guide</h4>
        <div className="space-y-2 text-sm text-gray-700">
          <div className="flex items-start gap-2">
            <span className="font-bold">Rt &gt; 1:</span>
            <span>Burnout spreading - each case creates multiple new cases</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-bold">Rt = 1:</span>
            <span>Stable state - burnout neither growing nor shrinking</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-bold">Rt &lt; 1:</span>
            <span>Burnout declining - system recovering naturally</span>
          </div>
        </div>
      </div>

      {/* Drill Down Button */}
      {onDrillDown && (
        <button
          onClick={onDrillDown}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          aria-label="View detailed burnout transmission network analysis"
        >
          View Burnout Transmission Network
        </button>
      )}

      {/* Framework Info */}
      <div className="mt-4 text-xs text-gray-600 bg-blue-50 rounded p-3">
        <strong>Burnout Epidemiology:</strong> Applies SIR (Susceptible-Infected-Recovered) model
        from infectious disease epidemiology to burnout spread. Rt (reproduction number) measures
        how many people one burned-out person affects. Uses network analysis to track stress
        transmission through the organization.
      </div>
    </div>
  );
};

export default BurnoutRtDisplay;
