'use client';

/**
 * Fragility Grid Component
 *
 * Displays a 28-day heatmap grid showing fragility levels per day.
 * Color-coded based on risk: green (safe), amber (warning), red (critical).
 */

import { DayData } from '../types';

interface FragilityGridProps {
  /** Array of day data */
  days: DayData[];
  /** Currently selected day */
  selectedDay: DayData;
  /** Callback when a day is selected */
  onSelectDay: (day: DayData) => void;
}

export function FragilityGrid({
  days,
  selectedDay,
  onSelectDay,
}: FragilityGridProps) {
  return (
    <div className="grid grid-cols-7 gap-2">
      {days.map((d) => {
        const isSelected = selectedDay.day === d.day;

        // Color logic based on fragility
        let baseClass =
          'bg-slate-900 border-slate-700 text-slate-500 hover:border-slate-500';
        if (d.fragility > 0.8) {
          baseClass =
            'bg-red-950/40 border-red-500/50 text-red-500 shadow-[0_0_10px_rgba(239,68,68,0.2)] animate-pulse';
        } else if (d.fragility > 0.4) {
          baseClass =
            'bg-amber-950/20 border-amber-600/50 text-amber-500';
        }

        if (isSelected) {
          baseClass = `${baseClass} ring-2 ring-white ring-offset-2 ring-offset-slate-900 z-10`;
        }

        return (
          <button
            key={d.day}
            onClick={() => onSelectDay(d)}
            className={`
              group relative aspect-square w-full rounded-sm border
              flex items-center justify-center text-[10px] font-bold
              transition-all duration-200 hover:scale-110 hover:z-20
              ${baseClass}
            `}
          >
            {d.day}
            {/* Mini indicator for SPOF */}
            {d.spof && (
              <div className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-current opacity-80" />
            )}

            {/* Tooltip on hover */}
            <div className="absolute bottom-full mb-2 hidden group-hover:block bg-slate-800 border border-slate-600 p-2 text-[9px] w-28 z-30 pointer-events-none whitespace-normal text-left shadow-xl rounded">
              <span className="block text-white font-semibold">Day {d.day}</span>
              <span className="text-slate-400">
                Fragility: {(d.fragility * 100).toFixed(0)}%
              </span>
              {d.spof && (
                <span className="block text-red-400 mt-1">SPOF: {d.spof}</span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}

export default FragilityGrid;
