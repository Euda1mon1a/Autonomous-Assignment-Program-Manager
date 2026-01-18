/**
 * Math Panel Component
 *
 * Displays the ACGME supervision calculation:
 * - Intern Load: count × 0.5 AT
 * - Resident Load: count × 0.25 AT
 * - FMIT Inpatient Requirement: +1
 *
 * Shows critical status when available faculty < required.
 */

"use client";

import React from "react";
import { Cpu } from "lucide-react";

import { MathPanelProps } from "../types";

export const MathPanel: React.FC<MathPanelProps> = ({
  availableFaculty,
  reqFaculty,
  totalAT,
  data,
}) => {
  const isCritical = availableFaculty < reqFaculty;

  return (
    <div className="absolute left-8 top-8 z-10 w-80 select-none rounded-sm border border-slate-800 bg-slate-950/90 p-6 font-mono text-slate-300 shadow-2xl backdrop-blur-xl">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2 text-cyan-400">
          <Cpu size={18} />
          <span className="text-xs font-bold tracking-[0.3em]">
            RESIDENCY LOGIC
          </span>
        </div>
        <div
          className={`rounded-full border px-2 py-0.5 text-[9px] ${
            isCritical
              ? "animate-pulse border-red-500 text-red-500"
              : "border-emerald-500 text-emerald-500"
          }`}
        >
          {isCritical ? "CRITICAL" : "NOMINAL"}
        </div>
      </div>

      <div className="space-y-5">
        {/* The Supervision Math */}
        <div className="space-y-2.5">
          <div className="flex justify-between text-[11px] text-slate-500">
            <span>INTERN LOAD ({data.interns} × 0.5)</span>
            <span className="text-slate-200">
              {(data.interns * 0.5).toFixed(2)} AT
            </span>
          </div>
          <div className="flex justify-between text-[11px] text-slate-500">
            <span>RESIDENT LOAD ({data.residents} × 0.25)</span>
            <span className="text-slate-200">
              {(data.residents * 0.25).toFixed(2)} AT
            </span>
          </div>
          <div className="flex justify-between border-t border-slate-800 pt-2 text-[11px] font-bold text-cyan-400">
            <span>SUBTOTAL AT LOAD</span>
            <span>{totalAT.toFixed(2)}</span>
          </div>
          <div className="flex justify-between pl-2 text-[11px] italic text-slate-400">
            <span>→ CEIL(AT) ROUND UP</span>
            <span className="text-slate-200">{Math.ceil(totalAT)}</span>
          </div>
          <div className="flex justify-between text-[11px] font-bold text-red-500">
            <span>FMIT INPATIENT REQ</span>
            <span>+1.00</span>
          </div>
        </div>

        {/* Status Card */}
        <div
          className={`border p-4 transition-colors duration-500 ${
            isCritical
              ? "border-red-600 bg-red-950/20"
              : "border-cyan-800/40 bg-cyan-900/5"
          }`}
        >
          <div className="mb-1 flex items-end justify-between">
            <span className="text-[10px] font-bold uppercase text-slate-500">
              Req Faculty
            </span>
            <span className="text-[10px] font-bold uppercase text-slate-500">
              Available
            </span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-light text-white">{reqFaculty}</span>
            <span
              className={`text-3xl font-bold ${
                isCritical ? "text-red-500" : "text-cyan-400"
              }`}
            >
              {availableFaculty}
            </span>
          </div>
          <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-slate-900">
            <div
              className={`h-full transition-all duration-500 ${
                isCritical ? "bg-red-500" : "bg-cyan-500"
              }`}
              style={{ width: `${(availableFaculty / 10) * 100}%` }}
            />
          </div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-3 gap-2 pt-2 text-[9px] text-slate-500">
          <div className="flex items-center gap-1.5">
            <div className="h-1.5 w-1.5 rounded-full bg-red-500" /> FAC
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-1.5 w-1.5 rounded-full bg-cyan-400" /> RES
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-1.5 w-1.5 rounded-full bg-white" /> INT
          </div>
        </div>
      </div>
    </div>
  );
};

export default MathPanel;
