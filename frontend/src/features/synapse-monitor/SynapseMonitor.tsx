"use client";

import React, { useState, useEffect, useMemo } from "react";
import { FALLBACK_PERSONNEL } from "./constants";
import { Personnel, SynapseMonitorProps } from "./types";
import { useSynapseData } from "./useSynapseData";
import {
  BrainIcon,
  MoonIcon,
  AlertIcon,
  PulseIcon,
} from "./components/Icons";
import FatiguePulse from "./components/FatiguePulse";
import CircadianMap from "./components/CircadianMap";
import PersonnelList from "./components/PersonnelList";

const SynapseMonitor: React.FC<SynapseMonitorProps> = ({
  personnel: propPersonnel,
  onPersonSelect,
  className = "",
}) => {
  // Fetch real data from the resilience health API
  const { personnel: apiPersonnel, isLoading, isError, systemMetrics } = useSynapseData();

  // Use API data, fall back to props, then to fallback data
  const personnel = useMemo(() => {
    if (propPersonnel && propPersonnel.length > 0) {
      return propPersonnel; // Props take precedence (for testing/storybook)
    }
    if (apiPersonnel && apiPersonnel.length > 0) {
      return apiPersonnel;
    }
    return FALLBACK_PERSONNEL;
  }, [propPersonnel, apiPersonnel]);

  const [selected, setSelected] = useState<Personnel | null>(null);
  const [time, setTime] = useState(new Date());

  // Update selected when personnel changes
  useEffect(() => {
    if (personnel.length > 0 && !selected) {
      setSelected(personnel[0]);
    }
  }, [personnel, selected]);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleSelect = (p: Personnel) => {
    setSelected(p);
    onPersonSelect?.(p);
  };

  // Show loading state
  if (isLoading && !selected) {
    return (
      <div className={`min-h-screen bg-[#020202] text-slate-400 p-4 md:p-8 font-mono ${className}`}>
        <div className="max-w-7xl mx-auto flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-[10px] text-slate-500 uppercase tracking-widest">
              Syncing Cognitive Metrics...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (isError && !selected) {
    return (
      <div className={`min-h-screen bg-[#020202] text-slate-400 p-4 md:p-8 font-mono ${className}`}>
        <div className="max-w-7xl mx-auto flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <AlertIcon className="w-8 h-8 text-red-500 mx-auto" />
            <p className="text-[10px] text-red-400 uppercase tracking-widest">
              Neural Link Interrupted - Using Cached Data
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Guard against null selected (shouldn't happen with fallback data)
  if (!selected) {
    return null;
  }

  const isCritical = selected.reserve < 40;
  const accentColor = isCritical ? "text-red-500" : "text-cyan-400";
  const accentBorder = isCritical
    ? "border-red-500/30"
    : "border-cyan-500/30";

  return (
    <div
      className={`min-h-screen bg-[#020202] text-slate-400 p-4 md:p-8 font-mono ${className}`}
    >
      <div className="max-w-7xl mx-auto space-y-8 md:space-y-12">
        {/* Header HUD */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-white/10 pb-6 gap-4">
          <div className="space-y-2">
            <div
              className={`flex items-center gap-3 ${accentColor} transition-colors duration-500`}
            >
              <BrainIcon className="w-6 h-6" />
              <h1 className="text-xl md:text-2xl font-bold tracking-[0.3em] uppercase">
                Synapse Monitor
              </h1>
            </div>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest pl-1 flex items-center gap-2">
              <span>Cognitive Fatigue & Bio-Metric Load Triage // 2026.v1</span>
              {apiPersonnel && apiPersonnel.length > 0 && (
                <span className="flex items-center gap-1 text-emerald-500">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                  LIVE
                </span>
              )}
              {isError && (
                <span className="flex items-center gap-1 text-amber-500">
                  <span className="w-1.5 h-1.5 bg-amber-500 rounded-full" />
                  CACHED
                </span>
              )}
            </p>
          </div>
          <div className="text-left md:text-right font-mono w-full md:w-auto flex flex-row md:flex-col justify-between md:justify-start items-end md:items-end">
            <div className="text-[10px] text-slate-600 mb-1 tracking-wider">
              LOCAL_ID: KANEOHE_HI
            </div>
            <div className="text-sm font-bold text-white tracking-widest tabular-nums">
              {time.toLocaleTimeString()}
            </div>
          </div>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
          {/* Left Column: List */}
          <aside className="lg:col-span-4 space-y-6">
            <div className="flex justify-between items-end px-2 border-b border-white/5 pb-2">
              <h2 className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">
                Personnel Triage
              </h2>
              <span className="text-[9px] text-slate-600 uppercase">
                n={personnel.length} Quantized Units
              </span>
            </div>
            <PersonnelList
              personnel={personnel}
              selected={selected}
              onSelect={handleSelect}
            />
          </aside>

          {/* Right Column: Detail View */}
          <div className="lg:col-span-8 space-y-6 lg:space-y-8">
            {/* Main Status Card */}
            <section
              className={`bg-white/[0.02] border ${accentBorder} p-6 md:p-10 relative overflow-hidden group transition-all duration-500`}
            >
              {/* Background Ambient Glow */}
              <div
                className={`absolute -right-20 -top-20 w-64 h-64 rounded-full blur-[100px] opacity-20 transition-colors duration-1000 ${isCritical ? "bg-red-600" : "bg-cyan-600"}`}
              />

              <div className="relative z-10 flex flex-col md:flex-row justify-between items-start mb-12 gap-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <div
                      className={`w-1.5 h-1.5 rounded-full animate-pulse ${isCritical ? "bg-red-500" : "bg-cyan-500"}`}
                    />
                    <div className="text-[10px] text-slate-500 uppercase tracking-widest">
                      Active Focus
                    </div>
                  </div>
                  <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tighter">
                    {selected.name}
                  </h2>
                  <div className="text-xs text-slate-600 mt-1 uppercase tracking-wider">
                    Unit: {selected.unit || "3rd Marine Reg / Log"}
                  </div>
                </div>
                <div className="text-left md:text-right">
                  <div className="text-[10px] text-slate-500 uppercase mb-2 tracking-widest">
                    Cognitive Reserve
                  </div>
                  <div
                    className={`text-5xl font-bold tracking-tighter transition-colors duration-300 ${isCritical ? "text-red-500" : "text-cyan-400"}`}
                  >
                    {selected.reserve}%
                  </div>
                </div>
              </div>

              <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
                <div className="space-y-8">
                  <div>
                    <div className="flex justify-between text-[10px] text-slate-500 uppercase mb-3">
                      <span className="flex items-center gap-2">
                        <PulseIcon className="w-3 h-3" /> Synaptic Noise
                      </span>
                      <span className="text-white font-mono">
                        {(100 - selected.reserve).toFixed(1)}Hz
                      </span>
                    </div>
                    <FatiguePulse
                      value={100 - selected.reserve}
                      isCritical={isCritical}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-black/40 border border-white/5 hover:border-white/10 transition-colors">
                      <div className="text-[9px] text-slate-600 uppercase mb-1">
                        Sleep Debt
                      </div>
                      <div className="text-xl font-bold text-slate-300">
                        +{selected.debt}h
                      </div>
                    </div>
                    <div className="p-4 bg-black/40 border border-white/5 hover:border-white/10 transition-colors">
                      <div className="text-[9px] text-slate-600 uppercase mb-1">
                        Acuity Bias
                      </div>
                      <div
                        className={`text-xl font-bold ${selected.acuity === "Critical" ? "text-red-400" : "text-slate-300"}`}
                      >
                        {selected.acuity}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-black/20 p-6 border border-white/5 space-y-4 flex flex-col justify-between">
                  <div>
                    <h3
                      className={`text-[10px] uppercase font-bold tracking-widest flex items-center gap-2 mb-4 ${isCritical ? "text-red-400" : "text-amber-400"}`}
                    >
                      <AlertIcon /> Predictive Drift
                    </h3>
                    <p className="text-[11px] text-slate-400 leading-relaxed italic border-l-2 border-white/10 pl-3">
                      {isCritical
                        ? '"Synaptic failure imminent. Recommend immediate removal from command chain. Procedural error probability > 85%."'
                        : '"Current synaptic trajectory suggests a 22% increase in procedural error rate over the next 12 hours. Recommend FMIT anchor hand-off."'}
                    </p>
                  </div>
                  <div className="pt-4 space-y-3 border-t border-white/5">
                    <div className="flex justify-between text-[9px] text-slate-600 uppercase">
                      <span>Reaction Latency</span>
                      <span className="text-slate-300">
                        +{Math.floor((100 - selected.reserve) * 2.4)}ms
                      </span>
                    </div>
                    <div className="flex justify-between text-[9px] text-slate-600 uppercase">
                      <span>Working Memory</span>
                      <span
                        className={
                          isCritical
                            ? "text-red-500 font-bold"
                            : "text-emerald-500"
                        }
                      >
                        {isCritical ? "Degraded" : "Nominal"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Secondary Visualization: Circadian */}
            <section className="bg-white/[0.02] border border-white/5 p-6 md:p-8">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
                <h2 className="text-[10px] text-slate-500 uppercase font-bold tracking-widest flex items-center gap-2">
                  <MoonIcon /> Circadian Alignment (72h Window)
                </h2>
                <div className="flex gap-4 text-[9px] text-slate-600">
                  <span className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 bg-cyan-500/50 rounded-full" />{" "}
                    Peak
                  </span>
                  <span className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 bg-red-500/30 rounded-full" />{" "}
                    Misalignment
                  </span>
                </div>
              </div>
              <CircadianMap reserve={selected.reserve} />
            </section>
          </div>
        </main>

        {/* Footer */}
        <footer className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-2">
          {systemMetrics?.crisisMode ? (
            <div className="text-[9px] font-mono tracking-widest uppercase text-center md:text-left animate-pulse">
              <span className="text-red-500 mr-2 font-bold">CRISIS MODE ACTIVE</span>
              Defense Level: {systemMetrics.defenseLevel} | Load Shedding: {systemMetrics.loadSheddingLevel}
            </div>
          ) : systemMetrics ? (
            <div className="text-[9px] font-mono tracking-widest uppercase text-center md:text-left opacity-60">
              <span className="text-slate-400 mr-2">STATUS:</span>
              {systemMetrics.overallStatus.toUpperCase()} |
              N-1: {systemMetrics.n1Pass ? "PASS" : "FAIL"} |
              N-2: {systemMetrics.n2Pass ? "PASS" : "FAIL"} |
              Util: {Math.round(systemMetrics.utilizationRate * 100)}%
            </div>
          ) : (
            <div className="text-[9px] font-mono tracking-widest uppercase text-center md:text-left opacity-40">
              <span className="text-red-500/50 mr-2">WARNING:</span> Circadian
              flip-flops in N-1 units are non-recoverable without 48h reset.
            </div>
          )}
          <div className="text-[9px] font-mono italic text-slate-600 opacity-40">
            &quot;The meat-ware is the ultimate bottleneck.&quot;
          </div>
        </footer>
      </div>
    </div>
  );
};

export default SynapseMonitor;
