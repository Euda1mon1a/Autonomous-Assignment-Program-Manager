/**
 * Entropy Controls Component
 *
 * Slider control for adjusting the entropy level of the system.
 * Entropy represents faculty attrition - as it increases:
 * - Positions become more jittered (wave function collapse)
 * - Faculty availability drops
 * - System approaches critical state
 */

"use client";

import React from "react";

import { EntropyControlsProps } from "../types";

export const EntropyControls: React.FC<EntropyControlsProps> = ({
  entropy,
  setEntropy,
  availableFaculty,
  reqFaculty,
}) => {
  const attritionCount = 10 - availableFaculty;
  const isCritical = availableFaculty < reqFaculty;

  return (
    <div className="absolute bottom-12 left-1/2 z-10 w-full max-w-md -translate-x-1/2 rounded border border-slate-800 bg-black/80 px-8 py-6 shadow-2xl backdrop-blur-md">
      {/* Labels */}
      <div className="mb-3 flex justify-between font-mono text-[11px] uppercase tracking-widest">
        <span className="text-cyan-400">System Coherence</span>
        <span
          className={
            isCritical ? "font-bold text-red-500" : "text-slate-500"
          }
        >
          Faculty Attrition (N-{attritionCount})
        </span>
      </div>

      {/* Slider */}
      <input
        type="range"
        min="0"
        max="0.95"
        step="0.01"
        value={entropy}
        onChange={(e) => setEntropy(parseFloat(e.target.value))}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-slate-800 accent-cyan-500"
      />

      {/* Scale labels */}
      <div className="mt-2 flex justify-between font-mono text-[9px] uppercase text-slate-600">
        <span>Deterministic State</span>
        <span>Probabilistic Chaos</span>
      </div>
    </div>
  );
};

export default EntropyControls;
