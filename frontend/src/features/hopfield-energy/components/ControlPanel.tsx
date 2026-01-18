/**
 * Control Panel Component
 *
 * Sliders and controls for the Hopfield energy visualization.
 */

'use client';

import { STATUS_CONFIG, LEGEND_ITEMS } from '../constants';
import type { ControlPanelProps } from '../types';

export function ControlPanel({
  coverage,
  balance,
  energy,
  status,
  isSettling,
  onCoverageChange,
  onBalanceChange,
  onToggleSettle,
}: ControlPanelProps) {
  const statusConfig = STATUS_CONFIG[status];

  return (
    <div className="absolute top-4 left-4 w-80 bg-slate-950/90 border border-slate-800 p-6 rounded-xl backdrop-blur-md text-white font-mono">
      {/* Header */}
      <h1 className="text-xl font-bold mb-1 bg-gradient-to-r from-green-400 to-amber-400 bg-clip-text text-transparent">
        Hopfield Energy Landscape
      </h1>
      <p className="text-xs text-slate-400 mb-4">
        Schedule stability as neural attractor dynamics
      </p>

      {/* Sliders */}
      <div className="space-y-4">
        {/* Coverage Slider */}
        <div>
          <label className="text-sm text-slate-300 flex justify-between">
            <span>Supervision Coverage</span>
            <span className="text-green-400">{Math.round(coverage)}%</span>
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={coverage}
            onChange={(e) => onCoverageChange(Number(e.target.value))}
            className="w-full mt-1 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-green-500"
          />
        </div>

        {/* Balance Slider */}
        <div>
          <label className="text-sm text-slate-300 flex justify-between">
            <span>Faculty Load Balance</span>
            <span className="text-amber-400">{Math.round(balance)}%</span>
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={balance}
            onChange={(e) => onBalanceChange(Number(e.target.value))}
            className="w-full mt-1 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
          />
        </div>

        {/* Status Section */}
        <div className="pt-2 border-t border-slate-700">
          <div className="flex justify-between text-sm text-slate-400 mb-2">
            <span>Energy Level:</span>
            <span className="font-mono text-yellow-400">{energy.toFixed(3)}</span>
          </div>

          <div
            className={`text-center text-sm font-semibold py-1.5 px-2 rounded mb-2 ${statusConfig.className}`}
          >
            {statusConfig.text}
          </div>

          <button
            onClick={onToggleSettle}
            className={`w-full py-2 px-4 rounded-lg font-semibold transition-all ${
              isSettling
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-gradient-to-r from-green-600 to-amber-500 hover:from-green-700 hover:to-amber-600'
            } shadow-lg`}
          >
            {isSettling ? 'PAUSE' : 'SETTLE (Gradient Descent)'}
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-slate-700 text-xs text-slate-500 space-y-1">
        {LEGEND_ITEMS.map((item, i) => (
          <p key={i} className="flex items-center gap-2">
            <span className={`inline-block w-3 h-3 rounded-sm ${item.color}`} />
            {item.label}
          </p>
        ))}
        <p className="pt-1 text-slate-600">Drag to rotate scene</p>
      </div>
    </div>
  );
}

export { ControlPanel as default };
