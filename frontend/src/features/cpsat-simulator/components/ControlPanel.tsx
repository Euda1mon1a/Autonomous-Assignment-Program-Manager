/**
 * Control Panel Component
 *
 * User input panel for:
 * - Prompting new optimization scenarios
 * - Refreshing AI explanations
 */

"use client";

import React, { useState } from "react";
import { ChevronRight } from "lucide-react";

import { ControlPanelProps } from "../types";

export const ControlPanel: React.FC<ControlPanelProps> = ({
  onScenarioPrompt,
  onRefreshExplain,
}) => {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    onScenarioPrompt(prompt);
    setPrompt("");
  };

  return (
    <div className="absolute bottom-8 left-8 z-10 w-80">
      <form
        onSubmit={handleSubmit}
        className="space-y-3 border border-white/10 bg-black/60 p-4 shadow-2xl backdrop-blur-md"
      >
        <div className="mb-1 text-[9px] uppercase tracking-widest text-slate-500">
          Neural Interface
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Redefine problem space..."
            className="flex-1 border border-white/10 bg-black/40 px-3 py-2 text-[11px] text-slate-200 transition-colors focus:border-cyan-500/50 focus:outline-none"
          />
          <button
            type="submit"
            className="border border-cyan-500/30 bg-cyan-900/40 px-3 py-2 transition-all hover:bg-cyan-500/20 active:scale-95"
          >
            <ChevronRight className="h-4 w-4 text-cyan-400" />
          </button>
        </div>

        <button
          type="button"
          onClick={onRefreshExplain}
          className="w-full border border-transparent py-1 text-center text-[10px] uppercase tracking-[0.2em] text-slate-500 transition-all hover:border-cyan-500/10 hover:text-cyan-400"
        >
          [ Recalibrate Heuristics ]
        </button>
      </form>
    </div>
  );
};

export default ControlPanel;
