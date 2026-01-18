/**
 * HUD Component
 *
 * Heads-up display showing real-time solver metrics:
 * - Global optimum (objective value)
 * - Optimality gap
 * - Search nodes (branches)
 * - Solver status
 * - AI narration history
 */

"use client";

import React from "react";

import { HudProps } from "../types";

export const HUD: React.FC<HudProps> = ({ metrics, history, loading }) => {
  return (
    <div className="pointer-events-none absolute left-8 top-8 z-10 w-80">
      <div className="space-y-6 border border-white/10 bg-black/60 p-6 shadow-2xl backdrop-blur-md">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-white/10 pb-4">
          <div className="h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
          <h1 className="text-[10px] font-bold uppercase tracking-[0.4em] text-white">
            System Architecture
          </h1>
        </div>

        <div className="space-y-4">
          {/* Objective value */}
          <div className="flex items-end justify-between">
            <span className="text-[10px] uppercase tracking-widest text-slate-500">
              Global Optimum
            </span>
            <span className="font-mono text-2xl font-bold text-cyan-400">
              {metrics.objective}
            </span>
          </div>

          {/* Optimality gap */}
          <div className="space-y-1">
            <div className="flex justify-between text-[9px] uppercase tracking-tighter">
              <span className="text-slate-500">Optimality Gap</span>
              <span className="text-white">{metrics.gap}</span>
            </div>
            <div className="h-[2px] w-full bg-white/5">
              <div
                className="h-full bg-cyan-500 transition-all duration-500"
                style={{ width: `${100 - parseFloat(metrics.gap)}%` }}
              />
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-4 border-t border-white/5 pt-4">
            <div>
              <div className="mb-1 text-[9px] uppercase text-slate-500">
                Search Nodes
              </div>
              <div className="text-sm font-bold text-slate-200">
                {metrics.branches.toLocaleString()}
              </div>
            </div>
            <div>
              <div className="mb-1 text-[9px] uppercase text-slate-500">
                State Vector
              </div>
              <div className="text-sm font-bold uppercase text-cyan-500">
                {metrics.status}
              </div>
            </div>
          </div>
        </div>

        {/* AI narration section */}
        <div className="border-t border-white/10 pt-4">
          <div className="mb-3 flex items-center gap-2 text-[9px] uppercase tracking-widest text-slate-500">
            <span className="h-1 w-1 rounded-full bg-cyan-500" />
            Heuristic Intel
          </div>
          <div className="h-32 space-y-3 overflow-y-auto pr-2">
            {history
              .filter((m) => m.role === "assistant")
              .slice(-3)
              .map((msg, i) => (
                <div
                  key={i}
                  className="text-[11px] italic leading-relaxed text-slate-400"
                >
                  {msg.content}
                </div>
              ))}
            {loading && (
              <div className="animate-pulse text-[10px] text-cyan-600">
                Consulting Core Processor...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HUD;
