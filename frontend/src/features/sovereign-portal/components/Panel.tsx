/**
 * Panel Component
 *
 * Individual panel wrapper for the command dashboard.
 */

'use client';

import { Maximize2, Minimize2 } from 'lucide-react';
import { STATUS_COLORS, STATUS_BG_COLORS } from '../constants';
import type { PanelProps } from '../types';

export function Panel({
  config,
  children,
  isExpanded = false,
  onToggleExpand,
}: PanelProps) {
  return (
    <div
      className={`
        bg-slate-800/80 border rounded-xl overflow-hidden transition-all
        ${isExpanded ? 'col-span-2 row-span-2' : ''}
        ${STATUS_BG_COLORS[config.status]}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div>
          <h3 className="text-sm font-semibold text-white">{config.label}</h3>
          <p className="text-xs text-slate-400">{config.description}</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full animate-pulse ${
                config.status === 'nominal'
                  ? 'bg-green-400'
                  : config.status === 'warning'
                    ? 'bg-amber-400'
                    : 'bg-red-400'
              }`}
            />
            <span
              className={`text-lg font-bold ${STATUS_COLORS[config.status]}`}
            >
              {config.value}
              <span className="text-xs text-slate-500 ml-1">{config.unit}</span>
            </span>
          </div>

          {/* Expand button */}
          {onToggleExpand && (
            <button
              onClick={onToggleExpand}
              className="p-1 hover:bg-slate-700 rounded transition-colors"
            >
              {isExpanded ? (
                <Minimize2 className="w-4 h-4 text-slate-400" />
              ) : (
                <Maximize2 className="w-4 h-4 text-slate-400" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">{children}</div>
    </div>
  );
}

export default Panel;
