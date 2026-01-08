'use client';

import { Hospital, Moon, Palmtree, User } from 'lucide-react';
import type { SituationalAwareness as SituationalAwarenessType, AttendingInfo } from './types';

interface SituationalAwarenessProps {
  data: SituationalAwarenessType;
  attending: AttendingInfo;
}

// Absence type display labels
const ABSENCE_LABELS: Record<string, string> = {
  vacation: 'VA',
  deployment: 'DEPLOY',
  tdy: 'TDY',
  medical: 'MED',
  family_emergency: 'EMERG',
  conference: 'CONF',
  bereavement: 'BEREAV',
  emergency_leave: 'EMERG',
  sick: 'SICK',
  convalescent: 'CONV',
  maternity_paternity: 'PARENT',
};

/**
 * Situational Awareness Section
 *
 * Shows who is NOT in clinic:
 * - FMIT (Family Medicine Inpatient Team)
 * - Night rotation
 * - Remote assignments (Hilo, Okinawa, Kapiolani)
 * - Absences (vacation, sick, deployment, etc.)
 *
 * Plus attending at-a-glance banner.
 */
export function SituationalAwareness({ data, attending }: SituationalAwarenessProps) {
  const { fmit_team, night_rotation, remote_assignments, absences = [] } = data;

  // Check if we have any situational awareness data to show
  const hasFMIT = fmit_team.attending || fmit_team.residents.length > 0;
  const hasNights = night_rotation.length > 0;
  const hasRemote = remote_assignments.length > 0;
  const hasAbsences = absences.length > 0;
  const hasAttending = attending.am || attending.pm;

  if (!hasFMIT && !hasNights && !hasRemote && !hasAbsences && !hasAttending) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Attending Banner */}
      {hasAttending && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-blue-800">
              <User className="w-5 h-5" />
              <span className="font-semibold">TODAY&apos;S ATTENDING:</span>
            </div>
            <div className="flex items-center gap-6 text-blue-900">
              <span>
                <span className="font-medium">AM:</span>{' '}
                {attending.am ? (
                  <span className="font-semibold">{attending.am.name}</span>
                ) : (
                  <span className="text-blue-600 italic">Not assigned</span>
                )}
              </span>
              <span className="text-blue-300">|</span>
              <span>
                <span className="font-medium">PM:</span>{' '}
                {attending.pm ? (
                  <span className="font-semibold">{attending.pm.name}</span>
                ) : (
                  <span className="text-blue-600 italic">Not assigned</span>
                )}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Situational Awareness Grid - FMIT, Away, Absences */}
      {(hasFMIT || hasNights || hasRemote || hasAbsences) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* FMIT Section */}
          {hasFMIT && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Hospital className="w-5 h-5 text-amber-600" />
                <h3 className="font-semibold text-amber-800">
                  FMIT (Inpatient Team)
                </h3>
              </div>
              <div className="space-y-2 text-sm">
                {fmit_team.attending && (
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-amber-200 text-amber-800 rounded text-xs font-medium">
                      AT
                    </span>
                    <span className="font-medium text-amber-900">
                      {fmit_team.attending.name}
                    </span>
                  </div>
                )}
                {fmit_team.residents.map((resident) => (
                  <div key={resident.id} className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs font-medium">
                      PGY-{resident.pgy_level}
                    </span>
                    <span className="text-amber-900">{resident.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Away Section - Nights + Remote + Absences Combined */}
          {(hasNights || hasRemote || hasAbsences) && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Moon className="w-5 h-5 text-purple-600" />
                <h3 className="font-semibold text-purple-800">Away Today</h3>
              </div>
              <div className="space-y-2 text-sm">
                {/* Night rotation */}
                {night_rotation.map((call) => (
                  <div key={`night-${call.person.id}`} className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-purple-200 text-purple-800 rounded text-xs font-medium">
                      {call.call_type === 'night_float' ? 'NF' : 'Nights'}
                    </span>
                    <span className="text-purple-900">{call.person.name}</span>
                    <span className="text-purple-600 text-xs">
                      ({call.person.pgy_level ? `PGY-${call.person.pgy_level}` : 'Faculty'})
                    </span>
                  </div>
                ))}
                {/* Remote assignments */}
                {remote_assignments.map((remote) => (
                  <div key={`remote-${remote.person.id}`} className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                      {remote.location}
                    </span>
                    <span className="text-purple-900">{remote.person.name}</span>
                    {remote.surrogate && (
                      <span className="text-xs text-purple-600">
                        → {remote.surrogate.name}
                      </span>
                    )}
                  </div>
                ))}
                {/* Absences */}
                {absences.map((absence) => (
                  <div key={`absence-${absence.person.id}`} className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-medium">
                      {ABSENCE_LABELS[absence.absence_type] || absence.absence_type.toUpperCase()}
                    </span>
                    <span className="text-purple-900">{absence.person.name}</span>
                    <span className="text-purple-600 text-xs">
                      ({absence.person.pgy_level ? `PGY-${absence.person.pgy_level}` : 'Faculty'})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
