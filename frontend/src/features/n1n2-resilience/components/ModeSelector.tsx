/**
 * Mode Selector Component
 *
 * Toggle between N-1 and N-2 resilience modes.
 */

'use client';

import { Shield, ShieldAlert } from 'lucide-react';
import type { ModeSelectorProps, ResilienceMode } from '../types';

export function ModeSelector({
  mode,
  onModeChange,
  absentCount,
}: ModeSelectorProps) {
  const modes: { id: ResilienceMode; label: string; description: string }[] = [
    {
      id: 'N-1',
      label: 'N-1',
      description: 'Single faculty absence tolerance',
    },
    {
      id: 'N-2',
      label: 'N-2',
      description: 'Dual faculty absence tolerance',
    },
  ];

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        {mode === 'N-1' ? (
          <Shield className="w-4 h-4 text-cyan-400" />
        ) : (
          <ShieldAlert className="w-4 h-4 text-purple-400" />
        )}
        <span className="text-sm font-semibold text-slate-200 uppercase tracking-wide">
          Resilience Mode
        </span>
      </div>

      <div className="flex gap-2">
        {modes.map((m) => {
          const isActive = mode === m.id;
          const isDisabled =
            m.id === 'N-1' && absentCount > 1;

          return (
            <button
              key={m.id}
              onClick={() => !isDisabled && onModeChange(m.id)}
              disabled={isDisabled}
              className={`
                flex-1 py-3 px-4 rounded-lg border-2 transition-all
                ${
                  isActive
                    ? m.id === 'N-1'
                      ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400'
                      : 'bg-purple-500/20 border-purple-500 text-purple-400'
                    : 'bg-slate-900 border-slate-600 text-slate-400 hover:border-slate-500'
                }
                ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="text-xl font-bold">{m.label}</div>
              <div className="text-xs opacity-70 mt-1">{m.description}</div>
            </button>
          );
        })}
      </div>

      {absentCount > 1 && mode === 'N-2' && (
        <p className="text-xs text-amber-400 mt-2">
          N-1 mode disabled: more than 1 absence simulated
        </p>
      )}
    </div>
  );
}

export default ModeSelector;
