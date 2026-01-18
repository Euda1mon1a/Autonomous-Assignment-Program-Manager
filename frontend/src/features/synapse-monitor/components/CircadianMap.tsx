"use client";

import React from "react";

interface CircadianMapProps {
  reserve: number;
}

const CircadianMap: React.FC<CircadianMapProps> = ({ reserve }) => {
  // 72 hour window
  const timePoints = Array.from({ length: 72 });

  return (
    <div className="h-32 w-full bg-black/40 relative rounded-sm border border-white/5 flex items-end px-4 gap-[2px] overflow-hidden group">
      {timePoints.map((_, i) => {
        // Mock circadian rhythm math
        const phase = i * 0.2 + reserve * 0.05;
        const amplitude = Math.sin(phase);
        const isPeak = amplitude > 0.5;
        const isMisaligned = i % 24 > 22 || i % 24 < 5; // Mock "night" hours

        let bgClass = "bg-white/5";
        if (isPeak) bgClass = "bg-cyan-500/40 group-hover:bg-cyan-400/50";
        if (isMisaligned && !isPeak) bgClass = "bg-red-500/20";

        return (
          <div
            key={i}
            className={`flex-1 transition-all duration-1000 ${bgClass}`}
            style={{
              height: `${30 + Math.sin(i * 0.3) * 20}%`,
              opacity: isMisaligned ? 0.5 : 1,
            }}
          />
        );
      })}

      {/* Time Markers */}
      <div className="absolute top-0 left-1/3 w-px h-full bg-white/10 border-r border-dashed border-white/20">
        <span className="absolute bottom-2 left-1 text-[8px] text-white/30">
          +24h
        </span>
      </div>
      <div className="absolute top-0 left-2/3 w-px h-full bg-white/10 border-r border-dashed border-white/20">
        <span className="absolute bottom-2 left-1 text-[8px] text-white/30">
          +48h
        </span>
      </div>

      {/* Current Time Indicator */}
      <div className="absolute top-0 left-0 h-full w-full bg-gradient-to-r from-black/80 via-transparent to-transparent pointer-events-none" />
    </div>
  );
};

export default CircadianMap;
