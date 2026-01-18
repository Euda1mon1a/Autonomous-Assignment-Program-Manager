"use client";

import React from "react";
import { Personnel } from "../types";

interface PersonnelListProps {
  personnel: Personnel[];
  selected: Personnel;
  onSelect: (p: Personnel) => void;
}

const PersonnelList: React.FC<PersonnelListProps> = ({
  personnel,
  selected,
  onSelect,
}) => {
  return (
    <div className="space-y-2 overflow-y-auto max-h-[600px] scrollbar-hide pr-2">
      {personnel.map((p) => {
        const isSelected = selected.name === p.name;

        // Risk Badge Color
        let badgeColor =
          "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
        if (p.risk === "Critical")
          badgeColor = "bg-red-500/10 text-red-500 border-red-500/20";
        else if (p.risk === "High")
          badgeColor = "bg-amber-500/10 text-amber-500 border-amber-500/20";
        else if (p.risk === "Med")
          badgeColor = "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";

        // Reserve Bar Color
        const barColor =
          p.reserve < 40
            ? "bg-red-500"
            : p.reserve < 70
              ? "bg-amber-500"
              : "bg-cyan-500";

        return (
          <button
            key={p.name}
            onClick={() => onSelect(p)}
            className={`w-full text-left p-3 border-l-2 transition-all duration-300 group relative overflow-hidden ${
              isSelected
                ? "bg-white/5 border-cyan-400 pl-4"
                : "bg-transparent border-transparent pl-3 hover:bg-white/[0.02] hover:pl-4 opacity-60 hover:opacity-100"
            }`}
          >
            <div className="flex justify-between items-center mb-2 relative z-10">
              <span
                className={`text-xs font-bold tracking-tight ${isSelected ? "text-white" : "text-slate-400 group-hover:text-slate-200"}`}
              >
                {p.name}
              </span>
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded-sm border ${badgeColor} uppercase tracking-wider font-mono`}
              >
                {p.risk}
              </span>
            </div>

            {/* Status Bar Background */}
            <div className="h-1 w-full bg-slate-900/50 rounded-full overflow-hidden relative z-10">
              <div
                className={`h-full transition-all duration-500 ${barColor}`}
                style={{ width: `${p.reserve}%` }}
              />
            </div>

            {/* Selection Highlight Glare */}
            {isSelected && (
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-transparent pointer-events-none" />
            )}
          </button>
        );
      })}
    </div>
  );
};

export default PersonnelList;
