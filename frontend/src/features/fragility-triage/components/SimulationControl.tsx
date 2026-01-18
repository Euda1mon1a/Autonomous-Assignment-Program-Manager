'use client';

/**
 * Simulation Control Component
 *
 * Provides "Black Swan" scenario injection buttons for stress-testing
 * the system and a reset button to restore coherence.
 */

import { Zap, RefreshCcw } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { SCENARIOS } from '../constants';
import { Scenario } from '../types';

interface SimulationControlProps {
  /** Callback when a scenario is injected */
  onInject: (scenario: Scenario) => void;
  /** Callback to reset the simulation */
  onReset: () => void;
  /** Current redundancy percentage */
  redundancy: number;
}

export function SimulationControl({
  onInject,
  onReset,
  redundancy,
}: SimulationControlProps) {
  return (
    <Card className="bg-slate-800 border-slate-700 h-full">
      <CardContent className="p-6 flex flex-col h-full">
        <h2 className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-6 border-b border-slate-700 pb-4">
          &ldquo;Black Swan&rdquo; Injector
        </h2>

        <div className="space-y-3 flex-1">
          {SCENARIOS.map((scenario) => (
            <button
              key={scenario.id}
              onClick={() => onInject(scenario)}
              className="w-full group relative overflow-hidden p-4 border border-slate-700 bg-slate-900/50 hover:bg-red-950/30 hover:border-red-500/50 transition-all duration-300 text-left rounded"
            >
              <div className="flex justify-between items-center mb-1 relative z-10">
                <span className="text-sm text-slate-300 font-semibold group-hover:text-red-400 tracking-wide">
                  {scenario.label}
                </span>
                <Zap
                  size={14}
                  className="text-slate-600 group-hover:text-red-500 transition-colors"
                />
              </div>
              <p className="text-[10px] text-slate-500 group-hover:text-red-400/70 relative z-10">
                Impact: -{scenario.impact}% Redundancy
              </p>
              <p className="text-[9px] text-slate-600 mt-1 relative z-10">
                {scenario.description}
              </p>

              {/* Hover effect background */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-red-900/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-in-out" />
            </button>
          ))}
        </div>

        <div className="mt-6 pt-6 border-t border-slate-700">
          <button
            onClick={onReset}
            className="w-full py-3 px-4 flex items-center justify-center gap-2 text-sm text-cyan-400 uppercase border border-cyan-500/30 hover:bg-cyan-500/10 hover:border-cyan-500/50 transition-all duration-300 tracking-widest rounded"
          >
            <RefreshCcw size={14} />
            Reset Coherence
          </button>

          {redundancy < 50 && (
            <div className="mt-4 p-3 bg-red-950/30 border border-red-500/30 text-red-400 text-xs text-center animate-pulse rounded">
              CRITICAL INSTABILITY DETECTED
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default SimulationControl;
