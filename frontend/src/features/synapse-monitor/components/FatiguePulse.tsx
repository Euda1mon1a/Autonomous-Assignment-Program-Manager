"use client";

import React, { useMemo } from "react";

interface FatiguePulseProps {
  value: number; // 0-100, where higher is more noise/fatigue
  isCritical: boolean;
}

const FatiguePulse: React.FC<FatiguePulseProps> = ({ value, isCritical }) => {
  // Generate static heights once to avoid jitter on re-renders
  const bars = useMemo(
    () => Array.from({ length: 30 }).map(() => Math.random() * 60 + 40),
    []
  );

  return (
    <div className="flex items-center gap-0.5 sm:gap-1 h-12 w-full overflow-hidden">
      {bars.map((height, i) => {
        const threshold = value / 100;
        const isActive = i / bars.length < threshold;

        // Color logic
        let barColorClass = "bg-slate-800";
        let opacity = 0.2;

        if (isActive) {
          opacity = 1;
          barColorClass = isCritical
            ? "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"
            : "bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]";
        }

        return (
          <div
            key={i}
            className={`w-1 md:w-1.5 rounded-full transition-all duration-500 ${barColorClass}`}
            style={{
              height: `${height}%`,
              opacity: opacity,
              transform: isActive ? `scaleY(${1 + Math.random() * 0.2})` : "none",
            }}
          />
        );
      })}
    </div>
  );
};

export default FatiguePulse;
