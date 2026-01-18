/**
 * Faculty Grid Component
 *
 * Clickable grid of faculty members for absence simulation.
 */

'use client';

import { User, UserX } from 'lucide-react';
import { CRITICALITY_COLORS, CRITICALITY_BORDER_COLORS } from '../constants';
import type { FacultyGridProps } from '../types';

export function FacultyGrid({
  faculty,
  absentFaculty,
  mode,
  onToggleAbsence,
}: FacultyGridProps) {
  const maxAbsences = mode === 'N-1' ? 1 : 2;
  const currentAbsences = absentFaculty.length;

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide">
          Faculty Roster
        </h3>
        <span className="text-xs text-slate-400">
          Click to simulate absence ({currentAbsences}/{maxAbsences} max)
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {faculty.map((member) => {
          const isAbsent = absentFaculty.includes(member.id);
          const canToggle = isAbsent || currentAbsences < maxAbsences;

          return (
            <button
              key={member.id}
              onClick={() => canToggle && onToggleAbsence(member.id)}
              disabled={!canToggle}
              className={`
                relative p-4 rounded-lg border-2 transition-all
                ${
                  isAbsent
                    ? 'bg-slate-900 border-slate-500 opacity-60'
                    : `bg-gradient-to-br ${CRITICALITY_COLORS[member.criticality]} ${CRITICALITY_BORDER_COLORS[member.criticality]}`
                }
                ${canToggle ? 'cursor-pointer hover:scale-105' : 'cursor-not-allowed'}
              `}
            >
              {/* Absent overlay */}
              {isAbsent && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg">
                  <UserX className="w-8 h-8 text-red-400" />
                </div>
              )}

              <div className={isAbsent ? 'opacity-50' : ''}>
                <div className="flex items-center gap-2 mb-2">
                  <User className="w-4 h-4 text-white/80" />
                  <span className="text-sm font-semibold text-white truncate">
                    {member.name}
                  </span>
                </div>

                <div className="text-xs text-white/70 space-y-1">
                  <div className="flex justify-between">
                    <span>{member.role}</span>
                    <span>{member.coverage}%</span>
                  </div>
                  <div className="text-white/50">{member.specialty}</div>
                </div>

                {/* Criticality indicator */}
                <div className="absolute top-2 right-2">
                  <span
                    className={`
                    inline-block w-2 h-2 rounded-full
                    ${member.criticality === 'critical' ? 'bg-white animate-pulse' : 'bg-white/50'}
                  `}
                  />
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-slate-700 flex flex-wrap gap-4 text-xs text-slate-400">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-gradient-to-br from-green-500 to-green-600" />
          <span>Low</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-gradient-to-br from-amber-500 to-amber-600" />
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-gradient-to-br from-orange-500 to-orange-600" />
          <span>High</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-gradient-to-br from-red-500 to-red-600" />
          <span>Critical</span>
        </div>
      </div>
    </div>
  );
}

export default FacultyGrid;
